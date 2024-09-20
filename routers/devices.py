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

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from models import Device, Token
from dependencies import get_auth_device
import tools

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
    #dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

@router.get("/discover/{uuid}") #, response_model=Device.Device)
async def get_device_infos(uuid: str) -> Device.Device:
    """Get device infos for current BLE uuid and generate device's token"""
    uuid = tools.uuidDecode(uuid) 
    if uuid:
        device = Device.getDeviceForUuid(uuid)
        device_token = Token.set_device_token('guest', uuid, 5)
        total_leds = device['nb_lines'] * device['nb_cols']
        device.update({"total_leds": total_leds})
        device.update({"login": Device.DeviceToken(device_token=device_token, url="/device-login")})
        return device 
    raise HTTPException(status_code=404)

# join device using token
@router.post("/login")
async def login_to_device(device_token: str) -> Token.AccessToken:
    """Get auth on device with device_token and generate access_token for datas"""
    uuid = Token.verify_device_token('guest', device_token)
    if uuid is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device token"
        )
    user = Device.getUserForUuid(uuid)
    device = Device.getDeviceForUuid(uuid)
    if not user:
        raise HTTPException(status_code=403)
    if not device:
        raise HTTPException(status_code=404)
    access_token_expires = Token.set_token_epxires(60)
    access_token = Token.create_access_token(
        data={"sub": user['id'], "device": device}, expires_delta=access_token_expires
    )
    return Token.AccessToken(access_token=access_token, token_type="bearer")

@router.get("/list")
async def get_devices_for_user(current_device: Annotated[str, Depends(get_auth_device)]) -> List[Device.Device]:
    """Get devices infos for current user"""
    user = current_device.get('user')
    devices = Device.getDevicesForUser(user['id']) 
    if devices:
        return devices
    raise HTTPException(status_code=404)