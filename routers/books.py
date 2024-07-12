from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Union
from models import Book, Position
from dependencies import get_auth_device
import tools

router = APIRouter()

@router.get("/book/{book_id}")
async def get_book(current_device: Annotated[str, Depends(get_auth_device)], book_id: Union[int, None] = None) -> Book.Book:
    """Get book for device bookshelf"""
    user = current_device.get('user')
    book = Book.getBook(book_id, user['id'])
    if not book:
        raise HTTPException(status_code=404)
    return book

@router.post("/book")
def create_book(current_device: Annotated[str, Depends(get_auth_device)], item: Book.Book):
    """Create new book for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book = Book.newBook(bookDict, user['id'], device['id'])
    # save tags
    Book.setTagsBook(book, user['id'], device['id'], None)
    return book

@router.put("/book/{book_id}")
def update_book(current_device: Annotated[str, Depends(get_auth_device)], book_id: int, item: Book.Book):
    """Update book data"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book = Book.updateBook(bookDict, book_id, user['id'], device['id'])
    # save tags
    Book.setTagsBook(book, user_id, device['id'], None)
    return book    

@router.get("/bookshelf")
async def get_books_in_bookshelf(current_device: Annotated[str, Depends(get_auth_device)], numshelf: Union[int, None] = None):
    """Get books list for current connected device"""
    device = current_device.get('device')
    user = current_device.get('user')
    elements = Book.getBooksForShelf(numshelf, device)
    return {"shelf_name": device['arduino_name'], "stored_books":elements}

@router.get("/books-order/{numshelf}")
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

@router.put("/books-order/{numshelf}")
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