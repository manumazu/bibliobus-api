from fastapi import FastAPI, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from models import Book, Device, User
import tools

app = FastAPI()

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

@app.get("/books/{book_id}", dependencies=[Depends(get_auth_user)])
def get_book(book_id: int):
    """Get book for device session"""
    user_id = 1
    result = Book.getBook(book_id, user_id)
    return {"book": result}

@app.get("/device/{uuid}")
def get_device(uuid):
    """get device infos for current arduino_name"""
    uuid = tools.uuidDecode(uuid) 
    if uuid:
        user_device = Device.getDeviceForUuid(uuid)
        user = Device.getUserForUuid(uuid)
        user_token = tools.setToken('guest', user['email'])
        total_leds = user_device['nb_lines'] * user_device['nb_cols']
        return {"device": user_device, "total_leds": total_leds, "token": user_token}
    raise HTTPException(status_code=404)

# login using user token
@app.post("/login")
def session_login(user_token: str):
    """/login?user_token=ssss1234234234"""
    user_id = tools.verifyToken('guest', user_token)
    if user_id is False:
        raise HTTPException(status_code=401)
    allow = User.getUser(user_id)
    if allow is False:
        raise HTTPException(status_code=401)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(key="Authorization", value=user_token)
    #SESSION_DB[RANDON_SESSION_ID] = username
    return response

@app.post("/logout")
async def session_logout(response: Response):
    response.delete_cookie(key="Authorization")
    #SESSION_DB.pop(RANDON_SESSION_ID, None)
    return {"status": "logged out"}