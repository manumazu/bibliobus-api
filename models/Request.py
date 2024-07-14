from fastapi import Path, HTTPException
from typing import Union, Annotated, List
from pydantic import BaseModel
from db import getMyDB
from models import Book, Position
import tools

mydb = getMyDB()

# biblio_app table definition

class Request(BaseModel):
  #id_app: int
  #id_node: int
  nodes: List
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