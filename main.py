from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from typing import Union, Annotated
import json
from models import Book, Device, User
import tools

app = FastAPI(title="Bibliobus API",
              description="Rest API to manage position datas from and to \"Bibus\" devices")

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
def get_book(request: Request, book_id: Union[int, None] = None):
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
def get_books_in_bookshelf(request: Request, numshelf: int | None = None):
    device = json.loads(request.cookies.get("Device"))
    shelfs = range(1,device['nb_lines']+1)
    if numshelf:
        shelfs = [numshelf]
    elements = {}
    stats = {}
    statics = {}
    for shelf in shelfs:
        books = Book.getBooksForRow(device['id'], shelf)
        statics[shelf] = Book.getStaticPositions(device['id'], shelf)   
        if books:
          statBooks = Book.statsBooks(device['id'], shelf)
          statPositions = Book.statsPositions(device['id'], shelf)
          positionRate = 0
          if statPositions['totpos'] != None:
            positionRate = round((statPositions['totpos']/device['nb_cols'])*100)
          stats[shelf] = {'nbbooks':statBooks['nbbooks'], 'positionRate':positionRate}        
          element = {}
          for row in books:     
            element[row['led_column']] = {'item_type':row['item_type'],'id':row['id'], \
            'title':row['title'], 'author':row['author'], 'position':row['position'], 'range':row['range'], \
            'borrowed':row['borrowed'], 'url':'/book/'+str(row['id'])}
            requested = Book.getRequestForPosition(device['id'], row['position'], shelf) #get requested elements from server (mobile will be set via SSE)
            if requested:
              element[row['led_column']]['requested']=True
          if statics[shelf]:
            for static in statics[shelf]:
              element[static['led_column']] = {'item_type':static['item_type'],'id':None, 'position':static['position']}
          elements[shelf] = sorted(element.items())
    return {"shelf_name": device['arduino_name'], "stored_books":elements}

@app.get("/device-discover/{uuid}")
def get_device_infos(uuid: str):
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
def login_to_device(user_token: str):
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
def get_devices_for_user(request: Request):
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