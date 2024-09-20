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

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Union
from models import Book, Location, Position, Tag
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

@router.get("/referencer")
def reference_books_with_api(current_device: Annotated[str, Depends(get_auth_device)], isbn: str, search_api: str) -> List[Book.Book]:
    """Retrieve books references using external API with ISBN code"""
    device = current_device.get('device')
    user = current_device.get('user')
    res = []
    '''Search books with googleapis api'''
    if search_api=='googleapis':
      query = "ISBN:\""+isbn+"\""
      data = Book.searchBookApi(query, 'googleapis')
      if 'items' in data:
        for item in data['items']:
          res.append(Book.formatBookApi('googleapis', item, isbn))
    '''Search books with openlibrary api'''
    if search_api=='openlibrary':
        query = "ISBN:"+isbn
        data = Book.searchBookApi(query, 'openlibrary')
        #print(data)      
        if query in data:
            res = [Book.formatBookApi('openlibrary', data[query], isbn)]
    return res

@router.post("/referencer")
def create_book_and_position(current_device: Annotated[str, Depends(get_auth_device)], item: Book.Book, \
    force_position: bool = False, book_width: Union[str, None] = None) -> Book.BookItem:
    """Create new book and position for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    bookDict = item.dict()
    book_id = Book.getBookByISBN(bookDict['isbn'], bookDict['reference'], user['id'])
    # save book if not present     
    if book_id:
        raise HTTPException(
            status_code=400,
            detail=f"A book already exists with id {book_id['id']}"
        )
    item = {}      
    # force width if not found or not set        
    if book_width is not None:
      bookDict['width'] = round(float(book_width))
    elif bookDict['width'] is None:
      bookDict['width'] = round(tools.setBookWidth(bookDict['pages']))
    # save book + tags 
    book = Book.newBook(bookDict, user['id'], device['id'])
    Tag.setTagsBook(bookDict, user['id'], device['id'], None)     
    book_id = book['id']
    item['book'] = book
    # save position if needed
    if force_position:
        lastPos = Position.getLastSavedPosition(device['id'])
        interval = tools.setBookInterval(book, device['leds_interval'])       
        if lastPos:
            position = lastPos['position']+1
            row = lastPos['row']
            led_column = lastPos['led_column']+interval
        else:
            position = 1
            row = 1
            led_column = 0
        Position.setPosition(device['id'], book_id, position, row, interval, 'book', led_column)
        address = Position.getPositionForBook(device['id'], book_id)
        if address:
            item['address'] = address
    return item

@router.post("/search")
async def search_books_in_bookshelf(current_device: Annotated[str, Depends(get_auth_device)], query: str) -> Book.BookSearch:
    """Search books fulltext for current connected device"""
    device = current_device.get('device')
    user = current_device.get('user')
    results = await Book.getSearchResults(device['id'], user['id'], query)    
    list_title = str(len(results))
    list_title += " books " if len(results) > 1 else " book "
    list_title += "for \""+query+"\""
    return {"list_title": list_title, "items":results}

@router.get("/shelf")
async def get_books_in_bookshelf(current_device: Annotated[str, Depends(get_auth_device)], numshelf: Union[int, None] = None) -> Book.BookShelf:
    """Get books list for current connected device"""
    device = current_device.get('device')
    user = current_device.get('user')
    elements = await Book.getBooksForShelf(numshelf, device, user)
    return {"list_title": device['arduino_name'], "books":elements}