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

from config import settings
import mysql.connector

def getMyDB():
	mydb = mysql.connector.connect(
	  host=settings.db_host,
	  user=settings.db_user,
	  password=settings.db_password,
	  database=settings.db_name
	)
	if mydb and not mydb.is_connected():
		mydb.reconnect()
	return mydb