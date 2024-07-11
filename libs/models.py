from pydantic import BaseModel
from typing import Dict


class Login(BaseModel):
    username: str
    password: str


class Register(BaseModel):
    email: str
    username: str
    password: str
    password_confirm: str


class Order(BaseModel):
    id_user: int = None
    articulos: Dict[int, int]
