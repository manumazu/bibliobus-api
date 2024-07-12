from fastapi import APIRouter, Depends
from typing import Annotated, List, Union
from models import Position
from dependencies import get_auth_device

router = APIRouter()

@router.get("/position/{book_id}")
async def get_position_for_item(current_device: Annotated[str, Depends(get_auth_device)], book_id: int) -> Position.Position:
    """Get book position in current bookshelf"""
    user = current_device.get('user')
    device = current_device.get('device')
    position = Position.getPositionForBook(device['id'], book_id)
    if not position:
        raise HTTPException(status_code=404)
    return position

@router.post("/position")
async def create_position_for_item(current_device: Annotated[str, Depends(get_auth_device)], item: Position.Position) -> Position.Position:
    """set new position for book : if exists, return error"""
    user = current_device.get('user')
    device = current_device.get('device')
    positionDict = item.dict()
    book_id = positionDict['id_item']
    position = Position.newPositionForBook(device, book_id, positionDict)
    return position

@router.delete("/position")
async def delete_position_for_item(current_device: Annotated[str, Depends(get_auth_device)], item: Position.Position):
    """delete position for given book"""
    user = current_device.get('user')
    device = current_device.get('device')
    positionDict = item.dict()
    book_id = positionDict['id_item']
    Position.removePositionForBook(device, book_id, positionDict)
    return {"status": "ok"}