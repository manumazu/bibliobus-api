from typing import Union
from pydantic import BaseModel
from db import mydb

# biblio_app table definition

class Module(BaseModel):
    id: int
    arduino_name: str
    id_ble: str
    nb_lines: int
    nb_cols: int
    strip_length: float
    leds_interval: float
    mood_color: Union[str, None] = None
    uuid: Union[str, None] = None
    mac: Union[str, None] = None

def getDeviceForUuid(uuid) :
	cursor = mydb.cursor(dictionary=True)
	cursor.execute("SELECT * FROM biblio_app WHERE id_ble=%s", [uuid])
	return cursor.fetchone()

def getUserForUuid(uuid):
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT bu.id, bu.email, bu.password, bu.firstname, ba.id as id_app, ba.arduino_name FROM biblio_user bu \
    INNER JOIN biblio_user_app bua ON bu.id = bua.id_user \
    INNER JOIN biblio_app ba ON bua.id_app = ba.id WHERE ba.id_ble=%s", [uuid])
  return cursor.fetchone()