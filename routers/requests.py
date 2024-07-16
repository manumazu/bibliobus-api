from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Annotated, List, Union
from asyncio import sleep
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

async def events_generator(app_id, source):
    requests = Request.getRequests(app_id, source, 'add')
    add_request = []
    # manage data for turning on leds
    for data in requests:
        add_request.append({'action':data['action'], 'row':data['row'], \
        'led_column':data['led_column'], 'interval':data['range'], 'id_tag':data['id_tag'], \
        'color':data['color'], 'id_node':data['id_node'], 'client':data['client'], 'date_add':data['date_add']})
        if source == 'mobile':
            Request.setRequestSent(app_id, data['id_node'], 1)
    add_request.sort(key=tools.sortPositions)
    blocks = tools.buildBlockPosition(add_request, 'add')
    for block in blocks:
        yield f"event: location\ndata: {block}\n\n"
        await sleep(.5)

@router.get("/events/{source}")
async def manage_requested_positions(current_device: Annotated[str, Depends(get_auth_device)], source: str = 'mobile'):
    """Used with SSE: check if request is sent to device, turn on light, and then remove request if leds are turned off"""
    user = current_device.get('user')
    device = current_device.get('device')    
    """We don't need to send request for mobile scope : events are already sent"""
    return StreamingResponse(events_generator(device['id'], source), media_type="text/event-stream")

@router.post("/tag/{tag_id}")
def create_request_for_tag_location(current_device: Annotated[str, Depends(get_auth_device)], tag_id: int, action: Union[str, None] = 'add', \
    client: Union[str, None] = 'server') -> List[Request.Request] :
    """Get book position in current books

    helf"""
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
