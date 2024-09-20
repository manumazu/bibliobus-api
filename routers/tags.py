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
from models import Book, Device, Location, Position, Tag
from dependencies import get_auth_device
import tools

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
    dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

@router.get("/books/{tag_id}")
async def get_books_for_tag(current_device: Annotated[str, Depends(get_auth_device)], tag_id: int) -> Tag.TagBooksList:
    """Get books list for given tag"""
    device = current_device.get('device')
    user = current_device.get('user')
    nodes = Tag.getBooksForTag(tag_id, device['id'])
    tag = Tag.getTagById(tag_id, user['id'])
    if not nodes:
        raise HTTPException(status_code=404)
    data = {}
    data['list_title'] = tag['tag']
    books = []
    for i in range(len(nodes)):
        book = Book.getBook(nodes[i]['id_node'], user['id'])
        address = Position.getPositionForBook(device['id'], book['id'])
        if address:
            requested = Location.getRequestForPosition(device['id'], address['position'], address['row'])
            if requested:
                book.update({'requested': True})
            books.append({'book':book, 'address':address, 'color':tag['color']})
    data['elements'] = books        
    return data

@router.get("/authors")
async def get_authors_in_bookshelf(current_device: Annotated[str, Depends(get_auth_device)]) -> Tag.TagListAuthors:
    """Get authors tags for current bookshelf"""
    device = current_device.get('device')
    user = current_device.get('user')    
    data = {}
    data['list_title'] = device['arduino_name']
    data['elements']=[]
    alphabet = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
    for i in range(len(alphabet)):
        items = await Tag.getAuthorsForApp(device['id'], alphabet[i])
        if items:
            '''set url for authenticate requesting location from app'''
            for j in range(len(items)):
                items[j]['url'] = f"/locations/tag/{items[j]['id']}"
                hasRequest = Location.getRequestForTag(device['id'], items[j]['id'])
                items[j]['hasRequest'] = hasRequest['nb_requests']
        data['elements'].append({'initial':alphabet[i],'items':items})
    return data

@router.get("/categories")
async def get_categories_for_bookshelf(current_device: Annotated[str, Depends(get_auth_device)]) -> Tag.TagListCategories:
    device = current_device.get('device')
    user = current_device.get('user')    
    categories = await Tag.getCategoriesForApp(user['id'], device['id'])
    data = {}
    data['list_title'] = device['arduino_name']
    if categories:
        for i in range(len(categories)):
            hasRequest = Location.getRequestForTag(device['id'], categories[i]['id'])
            categories[i]['url'] = f"/locations/tag/{categories[i]['id']}"
            categories[i]['hasRequest'] = hasRequest['nb_requests']
            if categories[i]['color'] is not None:
                colors = categories[i]['color'].split(",")
                categories[i]['red'] = colors[0]
                categories[i]['green'] = colors[1]
                categories[i]['blue'] = colors[2]
        data['elements']=categories
        #print(data)
        return data