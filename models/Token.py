from datetime import datetime, timedelta, timezone
from time import time
from typing import Union
from pydantic import BaseModel
import jwt
from jwt.exceptions import InvalidTokenError
from config import settings

# to get a string like this run:
# openssl rand -hex 32
ALGORITHM = "HS256"

class Token(BaseModel):
    access_token: str
    token_type: str

#generate generic token 
def set_device_token(role, uuid, expires_in=5):
  expires_delta = set_token_epxires(expires_in)
  expire = datetime.now(timezone.utc) + expires_delta
  return jwt.encode({role: uuid, 'exp': expire}, settings.secret_key, algorithm=ALGORITHM)

#verify token
def verify_device_token(role,token):
  try:
      allow = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])[role]
  except:
      return False
  return allow

def set_token_epxires(mins: int):
  return timedelta(minutes=mins)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
  to_encode = data.copy()
  if expires_delta:
      expire = datetime.now(timezone.utc) + expires_delta
  else:
      expire = datetime.now(timezone.utc) + timedelta(minutes=15)
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, settings.secret_key_access_token, algorithm=ALGORITHM)
  return encoded_jwt

def access_token_decode(token: str):
  return jwt.decode(token, settings.secret_key_access_token, algorithms=[ALGORITHM])