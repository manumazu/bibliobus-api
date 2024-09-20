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

from typing import Union
from pydantic import BaseModel
from db import getMyDB

mydb = getMyDB()

# biblio_app table definition

class User(BaseModel):
    id: int
    email: str
    hash_email: str
    password: str
    firstname: str
    lastname: Union[str, None] = None
    created_at: str
    updated_at: str

def get_user(user_id):
  mydb = getMyDB()  
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT id, email, password, firstname, lastname FROM biblio_user WHERE id=%s", [user_id])
  user = cursor.fetchone()
  if user:
    return user
  return false