from fastapi import Path
from typing import Union, Annotated, List
from pydantic import BaseModel, Field
from db import getMyDB
from models import Position, Request
import tools

class Book(BaseModel):
    # id_user: int
    # id_app: int
    isbn: Union[str, None] = None
    title: str
    subtitle: Union[str, None] = None
    keywords: Union[str, None] = None
    author: str
    editor: Union[str, None] = None
    year: Union[str, None] = None
    pages: Annotated[int, Path(title="Number of pages", ge=1)]
    reference: Union[str, None] = None
    description: Union[str, None] = None
    width: Annotated[Union[int, None], Path(title="Book width in millimeter", gte=10)] = None
    borrowed: Union[bool, None] = False
    requested: Union[bool, None] = False
    url: Union[str, None] = None

class BookItem(BaseModel):
    book: Book
    categories: Union[List[str], None] = None
    address: Union[Position.Position, None] = None

class shelfContent(BaseModel):
    led_column: int
    book: Book

class shelfStats(BaseModel):
    nbbooks: int
    positionRate: int

class shelfElement(BaseModel):
    numshelf: int
    items: List[shelfContent] 
    stats: shelfStats

class BookShelf(BaseModel):
    list_title: Annotated[Union[str, None], Path(title="Bookshelf name")] = Field(examples=["Biblio Demo"])
    books: List[shelfElement]

class BookSearch(BaseModel):
    list_title: Annotated[Union[str, None], Path(title="Bookshelf name")] = Field(examples=["Biblio Demo"])
    items: List[BookItem]   

async def getBooksForShelf(numshelf, device, user):
    ''' Get list of books order by positions '''
    shelfs = range(1,device['nb_lines']+1)
    if numshelf:
        shelfs = [numshelf]
    elements = []
    for shelf in shelfs:
        items = []
        books = getBooksForRow(device['id'], shelf)
        if books:
            items = formatBookList(books, user['id'], device['id'])
        # get stats elements for shelf
        statBooks = statsBooks(device['id'], shelf)
        statPositions = statsPositions(device['id'], shelf)
        positionRate = 0
        if statPositions['totpos'] != None:
            positionRate = round((statPositions['totpos']/device['nb_cols'])*100)
        stats = {'nbbooks':statBooks['nbbooks'], 'positionRate':positionRate}            
        elements.append({'numshelf': shelf, 'items': items, 'stats': stats})
    return elements

async def getSearchResults(app_id, user_id, query):
    items = []
    if len(query) > 2:
        results = searchBook(app_id, query)
    if results:
        items = formatBookList(results, user_id, app_id)
    return items

def formatBookList(books, user_id, app_id):
    items = []
    for element in books:
        book = getBook(element['id'], user_id)
        position = None
        # merge position for element if needed
        if 'position' not in element:
            position = Position.getPositionForBook(app_id, element['id'])
            element.update(position)
        book.update({'url':'/books/item/'+str(element['id']), 'borrowed':element['borrowed']})
        requested = Request.getRequestForPosition(app_id, element['position'], element['row'])
        if requested:
            book.update({'requested': True})
        items.append({'led_column': element['led_column'], 'book': book, 'address': position})
    return items

def getBook(book_id, user_id):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT `id`, `isbn`, `title`, `subtitle`, `ocr_keywords` as keywords, `author`, `editor`, `year`, `pages`, \
        `reference`, `description`, `width` FROM biblio_book where id=%s and id_user=%s",(book_id, user_id))
    return cursor.fetchone()

def getBooksForRow(app_id, numrow):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bb.`id`, bb.`title`, bb.`author`, bp.`position`, bp.`range`, bp.`row`, bp.`item_type`, bp.`led_column`,\
        bp.`borrowed` FROM biblio_book bb inner join biblio_position bp on bp.id_item=bb.id and bp.item_type='book'\
        inner join biblio_app app on bp.id_app=app.id where app.id=%s and bp.row=%s order by row, led_column",(app_id,numrow))
    #print(cursor._executed)
    return cursor.fetchall()

def statsBooks(app_id, numrow):
    """Get books quantity by row for module"""
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bp.`row`, count(bb.`id`) as nbbooks FROM biblio_book bb \
        inner join biblio_position bp on bp.id_item=bb.id and bp.item_type='book' \
        inner join biblio_app app on bp.id_app=app.id where app.id=%s and bp.`row`=%s", (app_id, numrow))
    return cursor.fetchone()

def newBook(book, user_id, app_id):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("INSERT INTO biblio_book (`id_user`, `id_app`, `isbn`, `title`, `subtitle`, `ocr_keywords`, `author`, `editor`, `year`, `pages`, \
        `reference`, `description`, `width`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (user_id, app_id, \
        book['isbn'], book['title'].strip(), book['subtitle'], book['keywords'], book['author'], book['editor'], book['year'], \
        book['pages'], book['reference'], book['description'], book['width']))
    mydb.commit()
    cursor.execute("SELECT LAST_INSERT_ID() as id")
    bookId = cursor.fetchone()
    book.update(bookId)
    return book

def updateBook(book, book_id, user_id, app_id):
    mydb = getMyDB()
    cursor = mydb.cursor()
    cursor.execute("UPDATE biblio_book SET `isbn`=%s, `title`=%s, `subtitle`=%s, `author`=%s, `editor`=%s, `year`=%s, `pages`=%s, \
      `reference`=%s, `description`=%s, `width`=%s, `ocr_keywords`=%s  WHERE id=%s", (book['isbn'], book['title'].strip(), \
       book['subtitle'], book['author'], book['editor'], book['year'], book['pages'], book['reference'], \
       book['description'], book['width'], book['keywords'], book_id))
    mydb.commit()
    return getBook(book_id, user_id)

def getStaticPositions(app_id, numrow):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT `led_column`, `range`, position, item_type FROM `biblio_position` \
        WHERE item_type='static' AND id_app=%s AND `row`=%s ORDER BY `position`", (app_id, numrow))
    return cursor.fetchall()

def statsPositions(app_id, numrow):
    """stats book positions by row for module"""
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bp.`row`, sum(bp.range) as totpos FROM biblio_position bp \
        inner join biblio_app app on bp.id_app=app.id \
        where app.id=%s and bp.`row`=%s", (app_id, numrow))#item_type='book' and inner join biblio_book bb on bb.id=bp.id_item \ 
    return cursor.fetchone()

async def getAuthorsForApp(app_id, letter):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    searchLetter = letter+"%"
    cursor.execute("SELECT bt.id, bt.tag, count(bb.id) as nbnode FROM `biblio_tags` bt \
        INNER JOIN biblio_tag_node btn ON bt.id = btn.id_tag \
        INNER JOIN biblio_book bb ON btn.id_node = bb.id \
        INNER JOIN biblio_position bp ON bb.id = bp.id_item and bp.item_type='book' \
        WHERE bt.id_taxonomy=2 and bp.id_app=%s and bt.tag like %s GROUP BY bt.id ORDER BY bt.tag", (app_id, searchLetter))
    return cursor.fetchall()

async def getCategoriesForApp(id_user, id_app):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bt.id, bt.tag, btu.color, count(bb.id) as nbnode FROM `biblio_tags` bt \
    INNER JOIN biblio_tag_node btn ON bt.id = btn.id_tag \
    INNER JOIN biblio_tag_user btu ON btn.id_tag = btu.id_tag \
    INNER JOIN biblio_book bb ON btn.id_node = bb.id \
    INNER JOIN biblio_position bp ON bb.id = bp.id_item and bp.item_type='book'\
    WHERE bt.id_taxonomy=1 and bp.id_app=%s and btu.id_user=%s GROUP BY bt.id ORDER BY bt.tag", (id_app, id_user))
    return cursor.fetchall()

def updateAppBook(app_id, item_id) :
  mydb = getMyDB()
  cursor = mydb.cursor()
  cursor.execute("UPDATE biblio_book SET id_app=%s WHERE id=%s", (app_id, item_id))
  mydb.commit()

def searchBook(app_id, keyword) :
  searchTerm = "%"+keyword+"%"
  mydb = getMyDB()
  cursor = mydb.cursor(dictionary=True)
  cursor.execute("SELECT * FROM biblio_search where id_app=%s and \
    (author like %s or title like %s or tags like %s)", (app_id, searchTerm, searchTerm, searchTerm))
  return cursor.fetchall()