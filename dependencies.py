from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import Token, User

device_auth_scheme = HTTPBearer()

def get_auth_device(token: HTTPAuthorizationCredentials = Depends(device_auth_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = Token.access_token_decode(token.credentials)
        #print(payload)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Token.InvalidTokenError:
        raise credentials_exception
    user = User.get_user(user_id)
    if user is None:
        raise credentials_exception
    return {"user": user, "device": payload.get("device")}