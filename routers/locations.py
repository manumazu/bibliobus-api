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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from typing import Annotated, List, Union
from asyncio import sleep
from models import Book, Device, Location, Position, Tag, Token
from dependencies import get_auth_device
import json
import tools

router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
    #dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

'''used when no color is customized : blue'''
color_default = '51, 102, 255'

def auth_device_token(uuid: str, device_token: str):
    """For Event source, verify that uuid has a valid session"""
    token_decode = Token.verify_device_token('guest', device_token)
    uuid_decode = tools.uuidDecode(uuid)
    if token_decode is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    if uuid_decode != token_decode:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device"
        )
    device = Device.getDeviceForUuid(uuid_decode)
    return device

async def events_generator(app_id, source):
    # get location requests data for turning on leds on device
    requests = Location.getRequests(app_id, 'add', source)
    data_to_add = []
    blocks = []
    for i, data in enumerate(requests):
        #build simple requests blocks for gaming
        if data['id_node'] == 0: 
            blocks.append({'action':data['action'], 'row':data['row'], 'index':i, 'start':data['led_column'], \
                'color':data['color'], 'id_tag':data['id_tag'],'interval':data['range'], 'nodes':[0], 'client':data['client']})
        #build position array for books requests
        else:
            data_to_add.append({'action':data['action'], 'row':data['row'], \
            'led_column':data['led_column'], 'interval':data['range'], 'id_tag':data['id_tag'], \
            'color':data['color'], 'id_node':data['id_node'], 'client':data['client'], 'date_add':data['date_add']})
        # set as sent for mobile (leds are already on)
        if source == 'mobile':
            Location.setRequestSent(app_id, data['id_node'], 1)
    # group positions by block
    data_to_add.sort(key=tools.sortPositions)
    blocks += tools.buildBlockPosition(data_to_add, 'add')

    # remove data request when leds are turned off from device
    requests = Location.getRequests(app_id, 'remove')
    data_to_remove = []
    if requests:
        #soft remove   
        for data in requests:
          #send remove for mobile only when request come from server 
          if (source == 'mobile' and data['client']=='server') or (source == 'server'):
            data_to_remove.append({'action':data['action'], 'row':data['row'], 'led_column':data['led_column'], \
          'interval':data['range'], 'id_tag':'', 'color':'', 'id_node':data['id_node'], 'client':data['client'], 'date_add':data['date_add']})
        data_to_remove.sort(key=tools.sortPositions)
        blocks += tools.buildBlockPosition(data_to_remove, 'remove')   
        #hard remove
        for data in requests:
            diff = tools.seconds_between_now(data['date_add'])
            #wait for other clients before remove
            if diff > 3:
                Location.removeRequest(app_id, data['led_column'], data['row'])

    # manage reset requests coming from distant app
    requests = Location.getRequests(app_id, 'reset', 'mobile')
    if requests:
        #soft remove   
        for data in requests:
            #send remove for mobile only when request come from server 
            if (source == 'mobile' and data['client']=='server') or (source == 'server'):
                blocks.append({'action':data['action'], 'client':data['client']})
        # clean reset request sent
        if source == 'mobile':
            Location.removeResetRequest(app_id) 

    return blocks

@router.get("/events/{source}")
async def manage_requested_positions_for_event_stream(device: Annotated[str, Depends(auth_device_token)], uuid: str, device_token: str, source: str = 'mobile') -> Location.EventLocations:
    """Used with SSE: check if location request is sent to device, turn on light, and then remove request if leds are turned off"""
    data = await events_generator(device['id'], source)
    data = json.dumps(data, default=str)
    msg = f"event: location\ndata: {data}\n\n"
    return StreamingResponse(msg, media_type="text/event-stream")

@router.post("/book/{book_id}")
def create_request_for_book_location(current_device: Annotated[str, Depends(get_auth_device)], book_id: int, color: Union[str, None] = None, \
  action: Union[str, None] = 'add', client: Union[str, None] = 'mobile') -> List[Location.Location] :
    """Get book position in current bookshelf and create location requests for lighting on (action 'add') or off leds (action 'remove')"""
    user = current_device.get('user')
    device = current_device.get('device')
    address = Position.getPositionForBook(device['id'], book_id)
    if address:
        position = []
        now = tools.getNow()
        dateTime = now.strftime("%Y-%m-%d %H:%M:%S")        
        Location.newRequest(device['id'], book_id, address['row'], address['position'], address['range'], \
         address['led_column'], 'book', client, action, dateTime, None, color)
        position.append({'action':action, 'row':address['row'], 'index': address['position'], 'start':address['led_column'], \
            'interval':address['range'], 'nodes': [book_id], 'borrowed':address['borrowed'], \
            'color':color, 'client':client, 'date_add':dateTime})
        return position

@router.post("/tag/{tag_id}")
def create_request_for_tag_location(current_device: Annotated[str, Depends(get_auth_device)], tag_id: int, action: Union[str, None] = 'add', \
    client: Union[str, None] = 'mobile') -> List[Location.Location] :
    """Get books position for tags in current bookshelf and create location requests for lighting on (action 'add') or off leds (action 'remove')"""
    user = current_device.get('user')
    device = current_device.get('device')
    nodes = Tag.getBooksForTag(tag_id, device['id'])
    tag = Tag.getTagById(tag_id, user['id'])

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
          Location.newRequest(device['id'], node['id_node'], address['row'], address['position'], address['range'], \
            address['led_column'], 'book', client, action, dateTime, tag_id, tag['color'])

          positions.append({'item':book['title'], 'action':action, 'row':address['row'], 'led_column':address['led_column'], \
          'interval':address['range'], 'id_tag':tag_id, 'color':tag['color'], 'id_node':node['id_node'], 'client':client, \
          'date_add':dateTime})

    '''sort elements for block build'''
    positions.sort(key=tools.sortPositions)
    blocks = tools.buildBlockPosition(positions, action)
    return blocks

def manage_position(device, item_id, position, action, color):
    now = tools.getNow()
    dateTime = now.strftime("%Y-%m-%d %H:%M:%S")
    Location.newRequest(device['id'], item_id, position['row'], position['start'], position['interval'], position['start'], 'book', 'server', \
        action, dateTime, None, color)
    position.update({'nodes':[item_id], 'index':position['start'], 'date_add': dateTime, 'action': action, 'client': 'server', 'color': color})
    return position

@router.put("/position/{item_id}")
def ask_position(current_device: Annotated[str, Depends(get_auth_device)], pos: Location.Position, item_id: str) -> Location.Location:
    """Turn on leds for position in the lighting system. Used for tiers API (could be retrieved with server send event)"""
    device = current_device.get('device')
    position = pos.dict()
    action = "add"
    color = "{},{},{}".format(position['red'], position['green'], position['blue'])
    return manage_position(device, item_id, position, action, color)

@router.delete("/position/{item_id}")
def del_position(current_device: Annotated[str, Depends(get_auth_device)], pos: Location.Position, item_id: str) -> Location.Location:
    """Turn off leds for position in the lighting system. Used for tiers API (could be retrieved with server send event)"""
    device = current_device.get('device')
    position = pos.dict()
    action = "remove"
    color = "-1"
    return manage_position(device, item_id, position, action, color)

@router.put("/reset")
def update_requests_for_reset(current_device: Annotated[str, Depends(get_auth_device)]):
    """Force reset all location requests for current device : event stream will delete all remaining requests"""
    device = current_device.get('device')
    Location.setRequestForRemove(device['id'])
    return {"status": "ok"}
