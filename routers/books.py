from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Union
from models import Book, Position
from dependencies import get_auth_device
import tools

router = APIRouter(
    prefix="/books",
    tags=["Books"],
    dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

@router.get("/item/{book_id}")
async def get_book_item(current_device: Annotated[str, Depends(get_auth_device)], book_id: Union[int, None] = None) -> Book.Book:
    """Get book for device bookshelf"""
    user = current_device.get('user')
    book = Book.getBook(book_id, user['id'])
    if not book:
        raise HTTPException(status_code=404)
    return book

@router.post("/item")
def create_book_item(current_device: Annotated[str, Depends(get_auth_device)], item: Book.Book):
    """Create new book for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book = Book.newBook(bookDict, user['id'], device['id'])
    # save tags
    Book.setTagsBook(book, user['id'], device['id'], None)
    return book

@router.put("/item/{book_id}")
def update_book_item(current_device: Annotated[str, Depends(get_auth_device)], book_id: int, item: Book.Book):
    """Update book data"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book = Book.updateBook(bookDict, book_id, user['id'], device['id'])
    # save tags
    Book.setTagsBook(book, user_id, device['id'], None)
    return book    

@router.get("/shelf")
async def get_books_in_bookshelf(current_device: Annotated[str, Depends(get_auth_device)], numshelf: Union[int, None] = None):
    """Get books list for current connected device"""
    device = current_device.get('device')
    user = current_device.get('user')
    elements = Book.getBooksForShelf(numshelf, device)
    return {"shelf_name": device['arduino_name'], "stored_books":elements}

@router.get("/authors")
async def get_authors_in_bookshelf(current_device: Annotated[str, Depends(get_auth_device)]):
    """Get authors tags for current bookshelf"""
    device = current_device.get('device')
    user = current_device.get('user')    
    data = {}
    data['list_title'] = device['arduino_name']
    data['elements']=[]
    alphabet = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
    for i in range(len(alphabet)):
        items = await Book.getAuthors(device['id'], alphabet[i])
        if items:
            '''set url for authenticate requesting location from app'''
            for j in range(len(items)):
                items[j]['url'] = f"/positions/request/tag/{items[j]['id']}"
                hasRequest = False #db.get_request_for_tag(session['app_id'], items[j]['id'])
                items[j]['hasRequest'] = hasRequest
        data['elements'].append({'initial':alphabet[i],'items':items})
    return data
  