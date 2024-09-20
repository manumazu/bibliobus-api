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
from models import Position
from dependencies import get_auth_device

router = APIRouter(
    prefix="/positions",
    tags=["Positions"],
    dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

@router.get("/item/{book_id}")
async def get_position_for_item(current_device: Annotated[str, Depends(get_auth_device)], book_id: int) -> Position.Position:
    """Get book position in current bookshelf"""
    user = current_device.get('user')
    device = current_device.get('device')
    position = Position.getPositionForBook(device['id'], book_id)
    if not position:
        raise HTTPException(status_code=404)
    return position

@router.post("/item")
async def create_position_for_item(current_device: Annotated[str, Depends(get_auth_device)], item: Position.Position) -> Position.Position:
    """set new position for book : if exists, return error"""
    user = current_device.get('user')
    device = current_device.get('device')
    positionDict = item.dict()
    book_id = positionDict['id_item']
    position = Position.newPositionForBook(device, book_id, positionDict)
    return position

@router.put("/item")
async def update_position_for_item(current_device: Annotated[str, Depends(get_auth_device)], item: Position.Position) -> Position.Position:
    """update position for book : be carefull, this is not for changing led position"""
    user = current_device.get('user')
    device = current_device.get('device')
    positionDict = item.dict()
    book_id = positionDict['id_item']
    Position.setPosition(device['id'], book_id, positionDict['position'], positionDict['row'], \
     positionDict['range'], 'book', positionDict['led_column'], 0, positionDict['borrowed'])
    position = Position.getPositionForBook(device['id'], book_id)
    return position

@router.delete("/item")
async def delete_position_for_item(current_device: Annotated[str, Depends(get_auth_device)], item: Position.Position):
    """delete position for given book"""
    user = current_device.get('user')
    device = current_device.get('device')
    positionDict = item.dict()
    book_id = positionDict['id_item']
    Position.removePositionForBook(device, book_id, positionDict)
    return {"status": "ok"}

@router.get("/order/{numshelf}")
async def get_items_order_for_shelf(current_device: Annotated[str, Depends(get_auth_device)], numshelf: int):
    """Get book positions for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    sortable = []
    positions = Position.getPositionsForShelf(device['id'], numshelf)
    for pos in positions:
        sortable.append({'book':pos['id_item'], 'position':pos['position'], 'fulfillment':int(pos['led_column']+pos['range']), \
            'led_column':pos['led_column'], 'shelf':numshelf})
    return {"numshelf": numshelf, "positions": sortable}

@router.put("/order/{numshelf}")
def update_items_order_for_shelf(current_device: Annotated[str, Depends(get_auth_device)], numshelf: int, \
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