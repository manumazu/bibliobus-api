from fastapi import Path, HTTPException
from typing import Union, Annotated, List
from pydantic import BaseModel, Field
from db import getMyDB
from models import Book, Position
import tools

mydb = getMyDB()

# biblio_app table definition

class Location(BaseModel):
  #id_app: int
  #id_node: int
  nodes: List[int]
  id_tag: Union[int, None] = None
  color: Annotated[Union[str, None], Path(title="RGB values")] = None
  node_type: Annotated[str, Path(title="Type of node")] = "book"
  index: Annotated[int, Path(title="Item Position in shelf ('column' in DB)")]
  row: Annotated[int, Path(title="Shelf nubmer")]
  interval: Annotated[int, Path(title="Leds interval ('range' in DB)")]
  date_add:str
  sent: Annotated[int, Path(title="SSE : is leds alight ?")] = 0
  start: Annotated[int, Path(title="Led's number in strip ('led_column' in DB)")]
  action: Annotated[str, Path(title="'add','remove','reset'")]
  client: Annotated[str, Path(title="'server','mobile'")]
  borrowed: Union[bool, None] = False

class EventLocations(BaseModel):
  event: Annotated[Union[str, None], Path(title="Envent Type")] = Field(examples=["location"])
  data: Union[Location, None] = None

#{'action': 'add', 'row': 1, 'index': 0, 'start': 7, 'id_tag': 1, 'color': '51, 102, 255', 'interval': 2, 'nodes': [1], 'client': 'server'}, 

def newRequest(app_id, node_id, row, column, interval, led_column, node_type, client, action, date_time, tag_id = None, color = None) :
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("INSERT INTO biblio_request (`id_app`, `id_node`, `node_type`, `row`, `column`, `range`, \
    `led_column`, `client`, `action`, `id_tag`, `color`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
    ON DUPLICATE KEY UPDATE `date_add`=%s, `range`=%s, `led_column`=%s, `client`=%s, `action`=%s, `color`=%s, `sent`=0", (app_id, node_id, node_type,\
     row, column, interval, led_column, client, action, tag_id, color, date_time, interval, led_column, \
     client, action, color))
  mydb.commit()

def getRequests(app_id, action, source = None):
  '''for requests coming from mobile, we don't need to send location generated on mobile : events are already sent to device'''  
  where = ''
  if action == 'add':
    where += " and `sent`=0"
  if source == 'mobile':
    where += " and `client`='server'"
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT * FROM biblio_request where id_app=%s and `action`=%s" + where, (app_id, action))
  #print(cursor._executed)
  return cursor.fetchall()

def getRequestForTag(app_id, tag_id) :
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT count(*) as nb_requests FROM biblio_request where id_app=%s and `id_tag`=%s \
    and `action`='add'", (app_id, tag_id))
  return cursor.fetchone()

def getRequestForPosition(app_id, position, row) :
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT * FROM biblio_request where id_app=%s and `column`=%s and `row`=%s \
    and `action`='add'", (app_id, position, row))
  return cursor.fetchone()

def setRequestSent(app_id, node_id, sent) :
  mydb = getMyDB()
  cursor = mydb.cursor()
  cursor.execute("UPDATE biblio_request SET `sent`=%s WHERE `id_app`=%s and `id_node`=%s \
    and `node_type` in ('book', 'static', 'reset')", (sent, app_id, node_id))
  mydb.commit()

def removeRequest(app_id, led_column, row) :
  mydb = getMyDB()
  cursor = mydb.cursor()
  cursor.execute("DELETE FROM biblio_request where id_app=%s and `led_column`=%s and `row`=%s", (app_id, led_column,row)) 
  mydb.commit()

def removeResetRequest(app_id) :
  mydb = getMyDB()
  cursor = mydb.cursor()
  cursor.execute("DELETE FROM biblio_request where id_app=%s and `action`='reset'",(app_id))
  mydb.commit()

def setRequestForRemove(app_id) :
  now = tools.getNow()
  mydb = getMyDB()
  cursor = mydb.cursor()
  cursor.execute("UPDATE biblio_request SET `action`='remove', `client`='mobile', `date_add`=%s WHERE `id_app`=%s \
    and action IN ('add', 'reset')", (now.strftime("%Y-%m-%d %H:%M:%S"), app_id))
  mydb.commit()
