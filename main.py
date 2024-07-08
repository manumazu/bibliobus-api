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

from fastapi import FastAPI, Request, Depends, HTTPException, Response, Query, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated, Any, List, Union
import json
from models import Book, Position, Device, Token, User
import tools

app = FastAPI(title="Bibliobus API",
              summary="Rest API to manage item positions from and to \"Bibus\" devices",
              version="0.1.0",
              contact={
                "name":"Bibliobus",
                "url":"https://bibliob.us/fr",
                "email":"contact@bibliob.us"
              },
              license_info={
                    "name": "GPLv3",
                    "url": "https://www.gnu.org/licenses/quick-guide-gplv3.html",
            })

origins = [
    "http://localhost",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"user": user, "device": payload['device']}

@app.get("/")
async def root():
    return {"message": "Welcome to Bibliobus API"}

@app.get("/book/{book_id}")
async def get_book(current_device: Annotated[str, Depends(get_auth_device)], book_id: Union[int, None] = None) -> Book.Book:
    """Get book for device bookshelf"""
    user = current_device.get('user')
    result = Book.getBook(book_id, user['id'])
    return result

@app.post("/book")
def create_book(current_device: Annotated[str, Depends(get_auth_device)], item: Book.Book):
    """Create new book for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book = Book.newBook(bookDict, user['id'], device['id'])
    # save tags
    Book.setTagsBook(book, user['id'], device['id'], None)
    return book

@app.put("/book/{book_id}")
def update_book(current_device: Annotated[str, Depends(get_auth_device)], book_id: int, item: Book.Book):
    """Update book data"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book = Book.updateBook(bookDict, book_id, user['id'], device['id'])
    # save tags
    Book.setTagsBook(book, user_id, device['id'], None)
    return book    

@app.get("/bookshelf")
async def get_books_in_bookshelf(current_device: Annotated[str, Depends(get_auth_device)], numshelf: Union[int, None] = None):
    """Get books list for current connected device"""
    device = current_device.get('device')
    user = current_device.get('user')
    elements = Book.getBooksForShelf(numshelf, device)
    return {"shelf_name": device['arduino_name'], "stored_books":elements}

@app.get("/books-order/{numshelf}")
async def get_books_order(current_device: Annotated[str, Depends(get_auth_device)], numshelf: int):
    """Get book positions for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    sortable = []
    positions = Position.getPositionsForShelf(device['id'], numshelf)
    for pos in positions:
        sortable.append({'book':pos['id_item'], 'position':pos['position'], 'fulfillment':int(pos['led_column']+pos['range']), \
            'led_column':pos['led_column'], 'shelf':numshelf})
    return {"numshelf": numshelf, "positions": sortable}

@app.put("/books-order/{numshelf}")
def update_books_order(current_device: Annotated[str, Depends(get_auth_device)], numshelf: int, \
    book_ids: List[int] = Query(None), reset_positions: Union[bool, None] = None):
    """Order positions and compute intervals for given books list ids"""
    device = current_device.get('device')
    user = current_device.get('user')
    # set positions and intervals for books
    positions = None
    if book_ids is not None:
        if reset_positions:
            Position.cleanPositionsForShelf(device['id'], numshelf)
        positions = Position.updatePositionsForShelf(user['id'], numshelf, book_ids, device)
    return {"numshelf": numshelf, "positions": positions}

@app.get("/device-discover/{uuid}", response_model=Device.Device)
async def get_device_infos(uuid: str) -> Any:
    """Get device infos for current BLE uuid and generate device's token"""
    uuid = tools.uuidDecode(uuid) 
    if uuid:
        device = Device.getDeviceForUuid(uuid)
        device_token = Token.set_device_token('guest', uuid, 5)
        total_leds = device['nb_lines'] * device['nb_cols']
        device.update({"total_leds": total_leds})
        device.update({"login": Device.DeviceToken(device_token=device_token)})
        return device 
    raise HTTPException(status_code=404)

# join device using token
@app.post("/device-login")
async def login_to_device(device_token: str):
    """Get auth on device with device_token and generate access_token for datas"""
    uuid = Token.verify_device_token('guest', device_token)
    if uuid is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device token"
        )
    user = Device.getUserForUuid(uuid)
    device = Device.getDeviceForUuid(uuid)
    if user and device:
        access_token_expires = Token.set_token_epxires(15)
        access_token = Token.create_access_token(
            data={"sub": user['id'], "device": device}, expires_delta=access_token_expires
        )
        return Token.Token(access_token=access_token, token_type="bearer")

@app.get("/devices")
async def get_devices_for_user(current_device: Annotated[str, Depends(get_auth_device)]):
    """Get devices infos for current user"""
    user = current_device.get('user')
    devices = Device.getDevicesForUser(user['id']) 
    if devices:
        return {"devices": devices}
    raise HTTPException(status_code=404)

# @app.post("/logout")
# async def session_logout():
#     #SESSION_DB.pop(RANDON_SESSION_ID, None)
#     return {"status": "logged out"}