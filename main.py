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

from fastapi import FastAPI, Request, Depends, HTTPException, Response, Query
from fastapi.responses import RedirectResponse
from typing import Union, Annotated, List
import json
from models import Book, Position, Device, User
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

def get_auth_user(request: Request):
    """verify that user has a valid session"""
    session_id = request.cookies.get("Authorization")
    if not session_id:
        raise HTTPException(status_code=401)
    # if session_id not in SESSION_DB:
    #     raise HTTPException(status_code=403)
    return True

@app.get("/")
async def root():
    return {"message": "Welcome to Bibliobus API"}

@app.get("/book/{book_id}", dependencies=[Depends(get_auth_user)])
async def get_book(request: Request, book_id: Union[int, None] = None):
    """Get book for device bookshelf"""
    user_id = request.cookies.get("UserId")
    result = Book.getBook(book_id, user_id)
    return {"book": result}

@app.post("/book", dependencies=[Depends(get_auth_user)])
def create_book(request: Request, item: Book.Book):
    """Create new book for current device"""
    user_id = int(request.cookies.get("UserId"))
    device = json.loads(request.cookies.get("Device"))
    bookDict = item.dict()
    book = Book.newBook(bookDict, user_id, device['id'])
    # save tags
    Book.setTagsBook(book, user_id, device['id'], None)
    return book

@app.put("/book/{book_id}", dependencies=[Depends(get_auth_user)])
def update_book(request: Request, book_id: int, item: Book.Book):
    """Update book data"""
    user_id = int(request.cookies.get("UserId"))
    device = json.loads(request.cookies.get("Device"))
    bookDict = item.dict()
    book = Book.updateBook(bookDict, book_id, user_id, device['id'])
    # save tags
    Book.setTagsBook(book, user_id, device['id'], None)
    return book    

@app.get("/bookshelf", dependencies=[Depends(get_auth_user)])
async def get_books_in_bookshelf(request: Request, numshelf: Union[int, None] = None):
    device = json.loads(request.cookies.get("Device"))
    elements = Book.getBooksForShelf(numshelf, device)
    return {"shelf_name": device['arduino_name'], "stored_books":elements}

@app.get("/books-order/{numshelf}", dependencies=[Depends(get_auth_user)])
async def get_books_order(request: Request, numshelf: int):
    """Get book positions for given shelf"""
    user_id = int(request.cookies.get("UserId"))
    device = json.loads(request.cookies.get("Device"))
    sortable = []
    positions = Position.getPositionsForShelf(device['id'], numshelf)
    for pos in positions:
        sortable.append({'book':pos['id_item'], 'position':pos['position'], 'fulfillment':int(pos['led_column']+pos['range']), \
            'led_column':pos['led_column'], 'shelf':numshelf})
    return {"numshelf": numshelf, "positions": sortable}

@app.put("/books-order/{numshelf}", dependencies=[Depends(get_auth_user)])
def update_books_order(request: Request, numshelf: int, book_ids: List[int] = Query(None), reset_positions: Union[bool, None] = None):
    """Order positions and compute intervals for given books list ids"""
    user_id = int(request.cookies.get("UserId"))
    device = json.loads(request.cookies.get("Device"))
    # set positions and intervals for books
    positions = None
    if book_ids is not None:
        if reset_positions:
            Position.cleanPositionsForShelf(device['id'], numshelf)
        positions = Position.updatePositionsForShelf(user_id, numshelf, book_ids, device)
    return {"numshelf": numshelf, "positions": positions}

@app.get("/device-discover/{uuid}")
async def get_device_infos(uuid: str):
    """Get device infos for current BLE uuid"""
    uuid = tools.uuidDecode(uuid) 
    if uuid:
        device = Device.getDeviceForUuid(uuid)
        user = Device.getUserForUuid(uuid)
        user_token = tools.setToken('guest', user['email'], uuid)
        total_leds = device['nb_lines'] * device['nb_cols']
        return {"device": device, "total_leds": total_leds, "token": user_token}
    raise HTTPException(status_code=404)

# join device using token
@app.post("/device-login")
async def login_to_device(user_token: str):
    """Open session on device with authenticated token"""
    verif = tools.verifyToken('guest', user_token)
    if verif is False:
        raise HTTPException(status_code=401)
    user_id, uuid = verif.split('|')
    user = User.getUser(user_id)
    device = Device.getDeviceForUuid(uuid)
    if user and device:
        response = RedirectResponse("/bookshelf", status_code=302)
        response.set_cookie(key="Authorization", value=user_token)
        response.set_cookie(key="UserId", value=user['id'])
        response.set_cookie(key="Device", value=json.dumps(device))
        #SESSION_DB[RANDON_SESSION_ID] = username
        return response
    raise HTTPException(status_code=401)

@app.get("/devices", dependencies=[Depends(get_auth_user)])
async def get_devices_for_user(request: Request):
    """Get devices infos for current user"""
    user_id = session_id = request.cookies.get("UserId")
    devices = Device.getDevicesForUser(user_id) 
    if devices:
        return {"devices": devices}
    raise HTTPException(status_code=404)

@app.post("/logout")
async def session_logout(response: Response):
    response.delete_cookie(key="Authorization")
    response.delete_cookie(key="UserId")
    response.delete_cookie(key="Device")
    #SESSION_DB.pop(RANDON_SESSION_ID, None)
    return {"status": "logged out"}