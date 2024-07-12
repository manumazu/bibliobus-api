from fastapi import Path, HTTPException
from typing import Union, Annotated
from pydantic import BaseModel
from db import getMyDB
from models import Book
import tools

mydb = getMyDB()

# biblio_app table definition

class Position(BaseModel):
    id_app: int
    id_item: int
    item_type: Annotated[str, Path(title="Type of item")] = "book"
    position: int
    row: int
    range: int
    shiftpos: Union[int, None] = None
    led_column: Annotated[int, Path(title="Defined by application", ge=1)] = 1
    borrowed: Union[bool, None] = False

def updatePositionsForShelf(user_id, numshelf, book_ids, device):
  ''' Compute intervals and update positions for items in current shelf '''
  sortable = []
  shift_position = 0

  # build list of new positions with ids already recorded
  new_positions = []
  current_positions = []
  bdd_positions = getPositionsForShelf(device['id'], numshelf)
  if bdd_positions is not None:
      for pos in bdd_positions:
          current_positions.append(str(pos['id_item']))
  # prevent not changing order for positions already in db 
  for book_id in current_positions:
    if book_id not in new_positions and book_id not in book_ids:
      new_positions.append(book_id)
  # prevent doublon
  for book_id in book_ids:
    if book_id not in new_positions:
      new_positions.append(book_id)

  # update all positions for current shelf
  pos = 0
  for book_id in new_positions:
    # shift book position for books not found in ocr result
    if str(book_id).startswith('empty'):
      shift_position = int(book_id.split('_')[1])
    # save position
    else:
      pos += 1
      updatePositionBeforeOrder(user_id, device['id'], book_id, numshelf, device, pos, shift_position)
      shift_position = 0

  #compute new leds interval
  positions = getPositionsForShelf(device['id'], numshelf)
  for pos in positions:
    led_columns_sum = getLedColumn(device['id'], pos['id_item'], numshelf, pos['position'])
    setLedColumn(device['id'], pos['id_item'], numshelf, led_columns_sum)  
    sortable.append({'book':pos['id_item'], 'position':pos['position'], 'fulfillment':int(led_columns_sum+pos['range']), \
      'led_column':led_columns_sum, 'shelf':numshelf})

  return sortable

def cleanPositionsForShelf(app_id, numshelf):
  mydb = getMyDB()
  cursor = mydb.cursor()
  cursor.execute("DELETE FROM biblio_position WHERE `item_type`='book' and `id_app`=%s and `row`=%s", (app_id, numshelf))
  mydb.commit()

def getPositionsForShelf(app_id, numshelf):
  mydb = getMyDB()  
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT * FROM biblio_position where id_app=%s and `row`=%s \
    and `item_type`<>'static' order by `position`", (app_id, numshelf))
  return cursor.fetchall()

''' update position order before computing books intervals sum ''' 
def updatePositionBeforeOrder(user_id, app_id, id_book, numshelf, device, new_position, shift_position = 0):
  # find current interval for book
  position = getPositionForBook(app_id, id_book, True)
  if position is not None:
    interval = position['range']
  else:
    book = Book.getBook(id_book, user_id)
    interval = tools.setBookInterval(book, device['leds_interval'])
  #save position + reinit led column + store shift led position before reorder
  setPosition(app_id, id_book, new_position, numshelf, interval, 'book', 0, shift_position)
  return getPositionForBook(app_id, id_book)

''' get book position for given app '''
def getPositionForBook(app_id, book_id, all_apps = False):
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  if all_apps:
    cursor.execute("SELECT * FROM biblio_position where id_item=%s and item_type='book'", [book_id])
  else:
    cursor.execute("SELECT * FROM biblio_position where id_app=%s and id_item=%s and item_type='book'", (app_id, book_id))
  return cursor.fetchone()

''' save or update item position '''
def setPosition(app_id, item_id, position, row, interval, item_type, led_column, shift_position = 0):
  mydb = getMyDB()
  cursor = mydb.cursor()
  cursor.execute("INSERT INTO biblio_position (`id_app`, `id_item`, `item_type`, \
      `position`, `row`, `range`, `led_column`, `shiftpos`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY \
      UPDATE position=%s, row=%s, `range`=%s, `led_column`=%s, `shiftpos`=%s", \
      (app_id, item_id, item_type, position, row, interval, led_column, shift_position, \
        position, row, interval, led_column, shift_position))
  mydb.commit()
  #udpate app for book item
  if item_type == 'book':
    Book.updateAppBook(app_id, item_id) 

def deletePosition(app_id, item_id, item_type, numrow):
  mydb = getMyDB()
  cursor = mydb.cursor()
  cursor.execute("DELETE FROM biblio_position WHERE `id_item`=%s and `item_type`=%s and `id_app`=%s and `row`=%s", \
    (item_id, item_type, app_id, numrow))
  mydb.commit()
  #udpate app for book item
  if item_type == 'book':
    Book.updateAppBook(app_id, item_id)  

def setLedColumn(app_id, item_id, row, led_column):
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("UPDATE biblio_position SET `led_column`=%s WHERE `id_app`=%s AND `id_item`=%s AND \
    `item_type`='book' AND `row`=%s", (led_column, app_id, item_id, row))
  mydb.commit()

'''compute sum of books intervals and shifted position (for missing books) for setting physical position'''
def getLedColumn(app_id, item_id, row, column):
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT (sum(`range`) + sum(`shiftpos`)) as `column` FROM `biblio_position` \
    WHERE `position`<%s  and id_app=%s and `row`=%s and id_item <> %s and item_type='book'",(column, app_id, row, item_id))
  #app.logger.info('get_led_column: %s', mysql['cursor']._last_executed)
  res = cursor.fetchone()
  if res and res['column'] is None:
    res['column'] = 0
  #check if book's real position must be shifted     
  shifted = getShiftedPositionForBook(app_id, row, item_id)    
  if shifted and shifted['shiftpos'] > 0:
    res['column'] += shifted['shiftpos']
  #check for static columns to shift book's real position     
  statics = getStaticPositions(app_id, row)    
  if statics is not None:
    for static in statics:
      if res['column'] >= static['led_column']:
        res['column'] += static['range']
  return res['column']

def getShiftedPositionForBook(app_id, row, item_id):
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT `shiftpos` FROM `biblio_position` \
    WHERE `item_type`='book' AND `id_app`=%s AND `row`=%s AND `id_item`=%s ORDER BY `position`", (app_id, row, item_id))
  return cursor.fetchone()

def getStaticPositions(app_id, row):
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT `led_column`, `range`, position, item_type FROM `biblio_position` \
    WHERE item_type='static' AND id_app=%s AND `row`=%s ORDER BY `position`", (app_id, row))
  return cursor.fetchall()
