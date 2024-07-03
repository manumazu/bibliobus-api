from typing import Union
from pydantic import BaseModel
from db import getMyDB

mydb = getMyDB()

# biblio_app table definition

class User(BaseModel):
    id: int
    email: str
    hash_email: str
    password: str
    firstname: str
    lastname: Union[str, None] = None
    created_at: str
    updated_at: str

def getUser(email):
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT id, email, password, firstname, lastname FROM biblio_user WHERE email=%s", [email])
  user = cursor.fetchone()
  if user:
    return user
  return false