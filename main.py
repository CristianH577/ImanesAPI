from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi import  HTTPException

import logging

from libs.models import Login, Register,Order
import libs.db as db

from typing import Annotated
import json

from datetime import datetime

#  -----------------------------------------------------------------------------------------
app = FastAPI()

logging.basicConfig(filename="./api.log", encoding="utf-8", level=logging.DEBUG)

origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def catch_exception_handler( exc: Exception):
    logging.error(exc)

    # error = JSONResponse(
    #     status_code=404, content={"error": "handle", "errorValue": str(exc)}
    # )
    # return error


# functions --------------------------------------------------------------------------------
async def validateAccountData(username: str = None, email: str = None):
    if email:
        query = "SELECT id_user FROM usuarios WHERE email = %s"
        check_email = await db.select(query, of="usuarios", data=[email])

        if check_email:
            return {"value": "email exist"}

    if username:
        query = "SELECT id_user FROM usuarios WHERE username = %s"
        check_username = await db.select(query, of="usuarios", data=[username])

        if check_username:
            return {"value": "username exist"}

    return False


# methods --------------------------------------------------------------------------------
# uvicorn main:app --reload
@app.get("/")
async def index():
    return "ON"


@app.get("/error")
async def error():
    raise HTTPException(status_code=404, detail="error de testeo")


@app.post("/register")
async def register(data: Register):
    validate = await validateAccountData(username=data.username, email=data.email)

    if validate:
        return validate

    query = "INSERT INTO usuarios (username,email,password) VALUES (%s,%s,%s)"
    results = await db.insert(
        query, data=[data.username, data.email, data.password], of="usuarios"
    )

    if results:
        return {"value": "register"}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron guardar los datos",
            },
        )


@app.post("/login")
async def login(data: Login):
    validate = await validateAccountData(username=data.username)

    if not validate:
        return {"value": "no user"}

    query = f"SELECT id_user FROM usuarios WHERE username = '{data.username}' AND email_confirm = 1"
    check_email = await db.select(query)

    if not check_email:
        return {"value": "email not confirm"}

    query = "SELECT id_user, rango FROM usuarios WHERE username = %s AND password= %s"
    check_password = await db.select(
        query, of="usuarios", data=list(data.dict().values())
    )
    if check_password:
        print(check_password)
        # id_user = check_password[0]["id_user"]
        return {"value": check_password[0]}
    else:
        return {"value": "wrong password"}


@app.get("/getUser")
async def getUser(id: int):
    data = {}

    query = f"SELECT username,email FROM usuarios WHERE id_user = {id}"
    cuenta = await db.select(query)
    data["cuenta"] = cuenta[0]

    query_personales = f"SELECT * FROM personales WHERE id_user = {id}"
    personales = await db.select(query_personales)
    if personales:
        data["personales"] = personales[0]

    query_pedidos = f"SELECT * FROM pedidos WHERE id_user = {id}"
    pedidos = await db.select(query_pedidos)
    if pedidos:
        for pedido in pedidos:
            del pedido["id_user"]
            pedido['articulos'] = json.loads(pedido['articulos'])
            pedido['estados'] = json.loads(pedido['estados'])
        data["pedidos"] = pedidos

    return {"value": data}


@app.put("/updateUserData")
async def updateUserData(data: Annotated[str, Body(...)]):
    data = json.loads(data)

    if data["id"] == "usuarios":
        try:
            username = data["fields"]["username"]
        except:
            username = None

        try:
            email = data["fields"]["email"]
        except:
            email = None

        if username or email:
            validate = await validateAccountData(username=username, email=email)

            if validate:
                return validate
        

    fields = data["fields"].keys()
    set = ""
    for field in fields:
        set = set + field + "=%s, "
    set = set[:-2]

    values = data["fields"].values()

    query = f"SELECT nombre FROM {data["id"]} WHERE id_user={data["id_user"]}"
    check_data = await db.select(query)
    
    if not check_data:
        query = f"INSERT INTO {data["id"]} (id_user) VALUES ({data["id_user"]})"
        await db.insert(query, allow_raise=False)

    query = f"UPDATE {data["id"]} SET {set} WHERE id_user={data["id_user"]}"
    response = await db.update(query, data=list(values))

    if response:
        return {"detail": "Cambios guardados."}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron actualizar los datos",
            },
        )


@app.put("/changePassword")
async def changePassword(data: Annotated[str, Body(...)]):
    data = json.loads(data)

    query = f"SELECT email FROM usuarios WHERE id_user={data["id_user"]} AND password='{data["fields"]["password"]}'"
    check_password = await db.select(query=query,data=[])
    if not check_password:
        return {"value": "wrong password"}
    
    query = f"UPDATE usuarios SET password='{data["fields"]["password_new"]}' WHERE id_user={data["id_user"]}"
    response = await db.update(query)

    if response:
        return {"detail": "Cambios guardados."}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudieron actualizar los datos",
            },
        )


@app.post("/addOrder")
async def addOrder(data: Order):
    estados=[["pendiente",""]]
    estados=json.dumps(estados)
    fecha_pedido=datetime.now()
    articulos=json.dumps(data.articulos)

    query = "INSERT INTO pedidos (id_user,articulos,estados,fecha_pedido) VALUES (%s,%s,%s,%s)"
    values=[
        data.id_user, 
        articulos, 
        estados,
        fecha_pedido
    ]
    results = await db.insert(query=query, data=values)

    if results:
        return {"detail": "Pedido enviado, pronto sera actualizado."}
    else:
        raise HTTPException(
            status_code=206,
            detail={
                "detail": "No se pudo realizar el pedido.",
            },
        )


@app.post("/getProductsData")
async def getProductsData(order: Order):
    print(order)
