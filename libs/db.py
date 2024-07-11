from fastapi import HTTPException

import MySQLdb
import locale


db_config = {
    "host": "localhost",
    "user": "root",
    "passwd": "",
    "db": "imanes-app",
}

locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")


def connect_db():
    try:
        conn = MySQLdb.connect(**db_config)
        return conn
    except MySQLdb.Error:
        raise HTTPException(
            status_code=400, detail="Error al conectar a la base de datos"
        )


async def handleAction(
    action: str, query: str, data: list = [], msg: str = None, allow_raise: bool = True
):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(query, data)

        if action != "select":
            conn.commit()

        if action == "select":
            return {"description": cursor.description, "rows": cursor.fetchall()}
        elif action == "insert":
            if cursor.rowcount > 0:
                return cursor.lastrowid
        elif action in ["delete", "update"]:
            if cursor.rowcount > 0:
                return cursor.rowcount

    except:
        if not msg:
            msg = "Error al manejar la base de datos"

        if allow_raise:
            raise HTTPException(status_code=400, detail=msg)

    finally:
        cursor.close()
        conn.close()

    return False


async def select(query: str, data: list = [], of: str = None, allow_raise: bool = True):
    msg = "Error al obtener datos"
    if of:
        msg += f": {of}"

    response = await handleAction("select", query, data, msg, allow_raise)

    if response:
        keys = [desc[0] for desc in response["description"]]
        response = [dict(zip(keys, row)) for row in response["rows"]]

    return response


async def insert(query: str, data: list = [], of: str = None, allow_raise: bool = True):
    msg = "Error al guardar datos"
    if of:
        msg += f": {of}"

    return await handleAction("insert", query, data, msg, allow_raise)


async def delete(query: str, data: list = [], of: str = None, allow_raise: bool = True):
    msg = "Error al eliminar datos"
    if of:
        msg += f": {of}"

    return await handleAction("delete", query, data, msg, allow_raise)


async def update(query: str, data: list = [], of: str = None, allow_raise: bool = True):
    msg = "Error al actualizar datos"
    if of:
        msg += f": {of}"

    return await handleAction("update", query, data, msg, allow_raise)
