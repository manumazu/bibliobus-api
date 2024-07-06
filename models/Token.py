from datetime import datetime, timedelta, timezone
from time import time
from typing import Union
from pydantic import BaseModel
import jwt
from jwt.exceptions import InvalidTokenError
from config import settings

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "a5b9d31f5b669fe8169e44a2e72105af09abaf9b5012ee1cba32f25278c29538"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str


#generate generic token 
def set_device_token(role, uuid, expires_in=600):
    return jwt.encode({role: uuid, 'exp': time() + expires_in}, settings.secret_key, algorithm='HS256')

#verify token
def verify_device_token(role,token):
  try:
      allow = jwt.decode(token, settings.secret_key, algorithms=['HS256'])[role]
  except:
      return False
  return allow

def set_token_epxires(minutes: int):
  return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def access_token_decode(token: str):
  return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])