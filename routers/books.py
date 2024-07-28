from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Union
from models import Book, Position, Request, Tag
from dependencies import get_auth_device
import tools

router = APIRouter(
    prefix="/books",
    tags=["Books"],
    dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

@router.get("/item/{book_id}")
async def get_book_item(current_device: Annotated[str, Depends(get_auth_device)], book_id: int) -> Book.BookItem:
    """Get book for device bookshelf"""
    device = current_device.get('device')
    user = current_device.get('user')
    item = {}
    item['book'] = Book.getBook(book_id, user['id'])
    if not item:
        raise HTTPException(status_code=404)
    item['categories'] = []
    tags = Tag.getTagForNode(book_id, 1)
    if tags:
        for i in range(len(tags)):
            item['categories'].append(tags[i]['tag'])        
    address = Position.getPositionForBook(device['id'], book_id)
    if address:
        item['address'] = address
    return item

@router.post("/item")
def create_book_item(current_device: Annotated[str, Depends(get_auth_device)], item: Book.Book):
    """Create new book for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book = Book.newBook(bookDict, user['id'], device['id'])
    # save tags
    Tag.setTagsBook(book, user['id'], device['id'], None)
    return book

@router.put("/item/{book_id}")
def update_book_item(current_device: Annotated[str, Depends(get_auth_device)], book_id: int, item: Book.Book):
    """Update book data"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book = Book.updateBook(bookDict, book_id, user['id'], device['id'])
    # save tags
    Tag.setTagsBook(book, user_id, device['id'], None)
    return book    

@router.get("/shelf")
async def get_books_in_bookshelf(current_device: Annotated[str, Depends(get_auth_device)], numshelf: Union[int, None] = None) -> Book.BookShelf:
    """Get books list for current connected device"""
    device = current_device.get('device')
    user = current_device.get('user')
    elements = await Book.getBooksForShelf(numshelf, device, user)
    return {"list_title": device['arduino_name'], "books":elements}