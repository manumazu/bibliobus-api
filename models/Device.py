from typing import Union
from pydantic import BaseModel
from db import getMyDB

# biblio_app table definition

class Device(BaseModel):
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

def getDeviceForUuid(uuid):
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT * FROM biblio_app WHERE id_ble=%s", [uuid])
  return cursor.fetchone()

def getUserForUuid(uuid):
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT bu.id, bu.email, bu.password, bu.firstname, ba.id as id_app, ba.arduino_name FROM biblio_user bu \
    INNER JOIN biblio_user_app bua ON bu.id = bua.id_user \
    INNER JOIN biblio_app ba ON bua.id_app = ba.id WHERE ba.id_ble=%s", [uuid])
  return cursor.fetchone()

def getDevicesForUser(user_id):
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT ba.*, TO_BASE64(ba.id_ble) as id_ble_encode, bu.id as user_id FROM biblio_app ba \
    INNER JOIN biblio_user_app bua ON bua.id_app = ba.id \
    INNER JOIN biblio_user bu ON bu.id=bua.id_user \
    WHERE bu.id=%s", [user_id])
  return cursor.fetchall()