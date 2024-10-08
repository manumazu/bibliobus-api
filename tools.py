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

from datetime import datetime
from config import settings
import hashlib, base64, re

def getNow():
  return datetime.now()

def getYear(datestr):
  try:
    datepub = datetime.strptime(datestr,'%b %d, %Y')
    return str(datepub.year)
  except ValueError:
    try:
      datepub = datetime.strptime(datestr,'%B %d, %Y')
      return str(datepub.year)
    except ValueError:
      try:
        datepub = datetime.strptime(datestr,'%Y-%m-%dT%H:%M:%S%z')
        return str(datepub.year)
      except ValueError: 
        try:
          datepub = datetime.strptime(datestr,'%Y-%m-%d')
          return str(datepub.year)
        except ValueError:
          return datestr

def seconds_between_now(d1):
    #d1 = datetime.strptime(str(d1), "%Y-%m-%d %H:%M:%S")
    d2 = getNow()
    return abs((d2 - d1).seconds)

def uuidDecode(encode):
  try:
    decode = base64.b64decode(encode)
    return decode.decode('utf-8')
  except ValueError:
    return False

def uuidEncode(string):
  try:
    encode = base64.b64encode(string.encode('utf-8'))
    return encode.decode('utf-8')
  except ValueError:
    return False

def getLastnameFirstname(names):
  lnfn=[]
  for name in names:
    namearr = name.split(' ')
    if len(namearr)>1:
      lnfn.append(' '.join(namearr[::-1])) #reverse names array
    else:
      lnfn.append(namearr[0])
  return lnfn

def setBookInterval(book, leds_interval):
  ''' compute interval with led strip spec '''
  ''' or compute range with book nb of pages '''
  if book['width'] and book['width'] > 0:
    book_width = book['width'] / 10 #convert mm to cm
    lrange = round(book_width/leds_interval)
    if lrange < 1:
      lrange = 1
  else:
    nb_pages =str(book['pages'])
    if nb_pages.strip() == '':
      lrange = 1
    elif int(nb_pages) < 200:
      lrange = 1
    elif int(nb_pages) > 1000:
      lrange = round(int(nb_pages)/400)
    else:
      lrange = round(int(nb_pages)/200)
  return lrange

def setBookWidth(pages):
  # use scale 120 pages for 1 cm 
  if pages <= 350:
    cm = pages/120
  # use scale 200 pages for 1 cm 
  elif pages > 350 and pages <= 500:
    cm = pages/200
  # use scale 350 pages for 1 cm 
  elif pages > 500:
    cm = pages/350
  if cm < 1:
    cm = 1
  return round(float(cm),2)*10

def sortIndexBlocks(elem):
  return elem['index']

def sortPositions(address):
  return address['row']*100+address['led_column']

def buildBlockPosition(positions, action):
  '''build blocks of nearby positions :'''
  '''agregate intervals and reduce messages to Arduino'''

  cpt = 0
  blockend = 0  
  block = {}
  blocks = []
  blockelem = []
  uniqelem = []

  #loop 1 : group nearby positions, and separate isolated postions 
  for i, pos in enumerate(positions): 

    #check if current pos is following the previous pos
    if int(pos['led_column']) == int(positions[i-1]['led_column'] + positions[i-1]['interval']) \
    and pos['color'] == positions[i-1]['color'] and pos['row'] == positions[i-1]['row'] : 

      prevItem = positions[i-1]

      #store node ids inside list
      if int(prevItem['id_node']) not in blockelem:  
        blockelem.append(int(prevItem['id_node']))
      if int(pos['id_node']) not in blockelem:        
        blockelem.append(int(pos['id_node']))

      #remove block first element from isolated list
      idx = prevItem['id_node'] if prevItem['id_node'] > 0 else (prevItem['row']+prevItem['led_column']+prevItem['interval'])
      if idx in uniqelem:
        uniqelem.remove(idx)

      #build block element : get first position and agragate intervals
      cpt+=1
      blockend += prevItem['interval']
      if cpt==1:
        block = {'action':action, 'row':pos['row'], 'index':i, 'start':prevItem['led_column'], \
        'color':pos['color'], 'id_tag':pos['id_tag'],}
      block.update({'interval':blockend+pos['interval'], 'nodes':blockelem, 'client':pos['client'], 'date_add':pos['date_add']})

      #populate blocks list
      if block not in blocks:
        blocks.append(block)
        
    #reinit for next block
    else:

      block = {}
      blockelem = []
      blockend = 0
      cpt = 0

      #store isolated elements: node_id for books, position for gaming
      idx = pos['id_node'] if pos['id_node'] > 0 else (pos['row']+pos['led_column']+pos['interval'])
      uniqelem.append(idx)
  
  #loop 2 : build response for isolated elements
  for i, pos in enumerate(positions):
    idx = pos['id_node'] if pos['id_node'] > 0 else (pos['row']+pos['led_column']+pos['interval'])
    for j in uniqelem:
      if j == idx:
        blocks.append({'action':action, 'row':pos['row'], 'index':i, 'start':pos['led_column'], \
          'id_tag':pos['id_tag'], 'color':pos['color'], 'interval':pos['interval'], \
          'nodes':[pos['id_node']], 'client':pos['client'], 'date_add':pos['date_add']})
  
  #print(blocks)

  #reset order for blocks:
  if(action=='remove'):
    blocks.sort(key=sortIndexBlocks, reverse=True)
  else:
    blocks.sort(key=sortIndexBlocks)

  return blocks
