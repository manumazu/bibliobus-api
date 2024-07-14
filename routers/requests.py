from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Union
from models import Book, Position, Request
from dependencies import get_auth_device
import tools

router = APIRouter(
    prefix="/requests",
    tags=["Requests"],
    dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

'''used when no color is customized : blue'''
color_default = '51, 102, 255'

@router.post("/tag/{tag_id}")
async def create_request_for_location(current_device: Annotated[str, Depends(get_auth_device)], tag_id: int, action: Union[str, None] = 'add', \
    client: Union[str, None] = 'server') -> List[Request.Request] :
    """Get book position in current bookshelf"""
    user = current_device.get('user')
    device = current_device.get('device')
    nodes = Book.getBooksForTag(tag_id, device['id'])
    tag = Book.getTagById(tag_id, user['id'])

    if tag['color'] is not None:
      colors = tag['color'].split(",")
      tag['red'] = colors[0]
      tag['green'] = colors[1]
      tag['blue'] = colors[2]
    else:
      tag['color'] = color_default

    positions = []
    now = tools.getNow()
    dateTime = now.strftime("%Y-%m-%d %H:%M:%S")
    if nodes:
      for node in nodes:
        address = Position.getPositionForBook(device['id'], node['id_node'])
        if address:
          book = Book.getBook(node['id_node'], user['id'])
          #save request
          Request.newRequest(device['id'], node['id_node'], address['row'], address['position'], address['range'], \
            address['led_column'], 'book', client, action, dateTime, tag_id, tag['color'])

          positions.append({'item':book['title'], 'action':action, 'row':address['row'], 'led_column':address['led_column'], \
          'interval':address['range'], 'id_tag':tag_id, 'color':tag['color'], 'id_node':node['id_node'], 'client':client, \
          'date_add':dateTime})

    '''sort elements for block build'''
    positions.sort(key=tools.sortPositions)
    blocks = tools.buildBlockPosition(positions, action)
    return blocks

