from fastapi import Path
from typing import Union, Annotated
from pydantic import BaseModel
from db import mydb

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
    width: Annotated[Union[int, None], Path(title="Book width in millimeter", ge=10)] = None

def getBook(book_id, user_id):
	cursor = mydb.cursor(dictionary=True)
	cursor.execute("SELECT `id`, `isbn`, `title`, `subtitle`, `ocr_keywords` as keywords, `author`, `editor`, `year`, `pages`, \
        `reference`, `description`, `width` FROM biblio_book where id=%s and id_user=%s",(book_id, user_id))
	return cursor.fetchone()

def getBooksForRow(app_id, numrow) :
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bb.`id`, bb.`title`, bb.`author`, bp.`position`, bp.`range`, bp.`row`, bp.`item_type`, bp.`led_column`,\
        bp.`borrowed` FROM biblio_book bb inner join biblio_position bp on bp.id_item=bb.id and bp.item_type='book'\
        inner join biblio_app app on bp.id_app=app.id where app.id=%s and bp.row=%s order by row, led_column",(app_id,numrow))
    return cursor.fetchall()

def statsBooks(app_id, numrow):
    """Get books quantity by row for module"""
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bp.`row`, count(bb.`id`) as nbbooks FROM biblio_book bb \
        inner join biblio_position bp on bp.id_item=bb.id and bp.item_type='book' \
        inner join biblio_app app on bp.id_app=app.id where app.id=%s and bp.`row`=%s", (app_id, numrow))
    return cursor.fetchone()

def saveBook(book, user_id, app_id, tags = None):
    if 'id' in book:
      bookId = newBook(book, user_id, app_id)
    else:
      bookId = newBook(book, user_id, app_id)
    print('bookId', bookId)
    book.update(bookId)
    return book
  #manage tags + taxonomy
  #author tags
  # authorTagids = []
  # if len(book['authors']) > 0:
  #   authorTags = tools.getLastnameFirstname(book['authors'])
  #   authorTagids = set_tags(authorTags,'Authors')
  #   if len(authorTagids)>0:
  #     set_tag_node(bookId, authorTagids)
  # #categories
  # if tags is not None :  
  #   clean_tag_for_node(bookId['id'], 1) #clean tags categories  before update
  #   catTagIds = set_tags(tags.split(','),'Categories')
  #   if len(catTagIds)>0:
  #     set_tag_node(bookId, catTagIds)
  #     set_tag_user(user_id, catTagIds)
  # return bookId

def newBook(book, user_id, app_id):
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("INSERT INTO biblio_book (`id_user`, `id_app`, `isbn`, `title`, `subtitle`, `ocr_keywords`, `author`, `editor`, `year`, `pages`, \
        `reference`, `description`, `width`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (user_id, app_id, \
        book['isbn'], book['title'].strip(), book['subtitle'], book['keywords'], book['author'], book['editor'], book['year'], \
        book['pages'], book['reference'], book['description'], book['width']))
    mydb.commit()
    cursor.execute("SELECT LAST_INSERT_ID() as id")
    return cursor.fetchone()

def updateBook(book, book_id, user_id, app_id):
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("UPDATE biblio_book SET `isbn`=%s, `title`=%s, `subtitle`=%s, `author`=%s, `editor`=%s, `year`=%s, `pages`=%s, \
      `reference`=%s, `description`=%s, `width`=%s, `ocr_keywords`=%s  WHERE id=%s", (book['isbn'], book['title'].strip(), \
       book['subtitle'], book['author'], book['editor'], book['year'], book['pages'], book['reference'], \
       book['description'], book['width'], book['keywords'], book_id))
    mydb.commit()
    return getBook(book_id, user_id)

def getStaticPositions(app_id, numrow):
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT `led_column`, `range`, position, item_type FROM `biblio_position` \
        WHERE item_type='static' AND id_app=%s AND `row`=%s ORDER BY `position`", (app_id, numrow))
    return cursor.fetchall()

def statsPositions(app_id, numrow):
    """stats book positions by row for module"""
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bp.`row`, sum(bp.range) as totpos FROM biblio_position bp \
        inner join biblio_app app on bp.id_app=app.id \
        where app.id=%s and bp.`row`=%s", (app_id, numrow))#item_type='book' and inner join biblio_book bb on bb.id=bp.id_item \ 
    return cursor.fetchone()

def getRequestForPosition(app_id, position, numrow) :
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM biblio_request where id_app=%s and `column`=%s and `row`=%s \
    and `action`='add'", (app_id, position, numrow))
    return cursor.fetchone()