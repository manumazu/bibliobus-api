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

from fastapi import Path
from typing import Union, Annotated, List
from pydantic import BaseModel, Field
from datetime import datetime
from db import getMyDB
from config import settings

class CustomCode(BaseModel):
    id: int
    title: str
    customvars: Union[str, None] = None
    date_add: datetime
    date_upd: datetime
    published: Union[bool, None] = False

class CustomCodes(BaseModel):
    list_title: Annotated[Union[str, None], Path(title="Blockly codes")] = Field(examples=["Your codes for Biblio Demo"])
    items: List[CustomCode]

class NativeEffects(BaseModel):
    list_title: Annotated[Union[str, None], Path(title="Native effects")] = Field(examples=["Effects for Biblio Demo"])
    items: List[str]

def getCustomCode(code_id, app_id, user_id):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT id, title, description, customvars, date_add, date_upd, published FROM biblio_customcode \
        where id_user=%s and id_app=%s and id=%s", (user_id, app_id, code_id))
    return cursor.fetchone()

def getCustomcodes(app_id, user_id, published_only = False) :
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    if published_only == True :
        cursor.execute("SELECT id, title, description, customvars, date_add, date_upd, published \
         FROM biblio_customcode where id_user=%s and id_app=%s and published=1 \
         and description='blockly workspace' order by `position`", (user_id, app_id))    
    else :
        cursor.execute("SELECT id, title, description, customvars, date_add, date_upd, published \
            FROM biblio_customcode where id_user=%s and id_app=%s \
            and description='blockly workspace' order by `position`", (user_id, app_id))
    return cursor.fetchall()

def getCustomcolors(app_id, user_id) :
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT id, title, coordinates, date_add, date_upd FROM biblio_customcolors \
        where id_user=%s and id_app=%s", (user_id, app_id))
    dbcoords = cursor.fetchone()
    if(dbcoords and dbcoords['coordinates']!='' and dbcoords['coordinates']!='{}'):
        return dbcoords