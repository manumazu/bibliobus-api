from datetime import datetime
from time import time
from config import settings
import hashlib, base64, re
import jwt

def getNow():
  return datetime.now()

def uuidDecode(encode):
  try:
    decode = base64.b64decode(encode)
    return decode.decode('utf-8')
  except ValueError:
    return False

def uuidEncode(string):
  try:
    encode = base64.b64encode(string.encode('utf-8'))
    return encode.decode('utf-8')
  except ValueError:
    return False    

#generate generic token 
def setToken(role, email, expires_in=600):
    return jwt.encode({role: email, 'exp': time() + expires_in}, settings.secret_key, algorithm='HS256')

#verify token
def verifyToken(role,token):
    try:
        allow = jwt.decode(token, settings.secret_key, algorithms=['HS256'])[role]
    except:
        return False
    return allow