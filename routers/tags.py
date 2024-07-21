from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Union
from models import Book, Device, Position, Request, Tag
from dependencies import get_auth_device
import tools

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
    dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

@router.get("/books/{tag_id}")
async def get_books_for_tag(current_device: Annotated[str, Depends(get_auth_device)], tag_id: int):
    """Get books list for given tag"""
    device = current_device.get('device')
    user = current_device.get('user')
    nodes = Tag.getBooksForTag(tag_id, device['id'])
    tag = Tag.getTagById(tag_id, user['id'])
    if not nodes:
        raise HTTPException(status_code=404)
    data = {}
    data['list_title'] = device['arduino_name']
    books = []
    for i in range(len(nodes)):
        book = Book.getBook(nodes[i]['id_node'], user['id'])
        books.append({'book':book})
        app_modules = Device.getDevicesForUser(user['id'])
        for module in app_modules:
            address = Position.getPositionForBook(module['id'], book['id'])
            if address:
                hasRequest = Request.getRequestForPosition(module['id'], address['position'], address['row'])
                books[i]['address'] = address
                books[i]['device'] = {'arduino_name': module['arduino_name'], 'uuid_encode': tools.uuidEncode(module['id_ble']), \
                    'app_id': module['id'], 'app_uuid': module['uuid'], 'app_mac': module['mac']}
                books[i]['hasRequest'] = hasRequest
                if tag['color'] is not None:
                    books[i]['color'] = tag['color']
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
                items[j]['url'] = f"/requests/tag/{items[j]['id']}"
                hasRequest = Request.getRequestForTag(device['id'], items[j]['id'])
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
            hasRequest = Request.getRequestForTag(device['id'], categories[i]['id'])
            categories[i]['url'] = f"/requests/tag/{categories[i]['id']}"
            categories[i]['hasRequest'] = hasRequest['nb_requests']
            if categories[i]['color'] is not None:
                colors = categories[i]['color'].split(",")
                categories[i]['red'] = colors[0]
                categories[i]['green'] = colors[1]
                categories[i]['blue'] = colors[2]
        data['elements']=categories
        #print(data)
        return data