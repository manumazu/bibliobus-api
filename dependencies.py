#==============================================================================
# Copyright (C) 2024  Emmanuel Mazurier <contact@bibliob.us>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#==============================================================================

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