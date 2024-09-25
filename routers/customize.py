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
from models import Customize
from dependencies import get_auth_device
import json
import tools

router = APIRouter(
    prefix="/customize",
    tags=["Custom Colors"],
    dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

@router.get("/listcodes")
async def get_codes_list(current_device: Annotated[str, Depends(get_auth_device)]) -> Customize.CustomCodes:
    """Get list of published custom codes for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    codelist = Customize.getCustomcodes(device['id'], user['id'], True)
    return {"list_title": f"Your codes for {device['arduino_name']}", "items":codelist}

@router.get("/code/{code_id}")
async def get_code(current_device: Annotated[str, Depends(get_auth_device)], code_id: int) -> Customize.CustomCode:
    """Get custom code for current device"""
    device = current_device.get('device')
    user = current_device.get('user')
    return Customize.getCustomCode(code_id, device['id'], user['id'])

@router.get("/effects")
async def get_native_effects(current_device: Annotated[str, Depends(get_auth_device)]) -> Customize.NativeEffects:
    """Get native light effects"""
    device = current_device.get('device')
    user = current_device.get('user')    
    effects = [ 'rainbow', 'rainbowWithGlitter', 'confetti', 'sinelon' , 'juggle', 'bpm', 'snowSparkle', 'fadeOut' ]
    return {"list_title": f"Effects for {device['arduino_name']}", "items":effects}