from typing import Union
from pydantic import BaseModel
from db import mydb

class Book(BaseModel):
    id: int
    id_user: int
    id_app: int
    isbn: Union[str, None] = None
    title: str
    subtitle: Union[str, None] = None
    ocr_keywords: Union[str, None] = None
    author: str
    editor: Union[str, None] = None
    year: Union[str, None] = None
    pages: Union[str, None] = None 
    reference: Union[str, None] = None
    description: Union[str, None] = None
    width: Union[int, None] = None

def getBook(book_id, user_id):
	cursor = mydb.cursor(dictionary=True)
	cursor.execute("SELECT * FROM biblio_book where id=%s and id_user=%s",(book_id, user_id))
	return cursor.fetchone()

def getBooksForRow(app_id, numrow) :
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bb.`id`, bb.`title`, bb.`author`, bp.`position`, bp.`range`, bp.`row`, bp.`item_type`, bp.`led_column`,\
        bp.`borrowed` FROM biblio_book bb inner join biblio_position bp on bp.id_item=bb.id and bp.item_type='book'\
        inner join biblio_app app on bp.id_app=app.id where app.id=%s and bp.row=%s order by row, led_column",(app_id,numrow))
    return cursor.fetchall()

def getStaticPositions(app_id, numrow):
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT `led_column`, `range`, position, item_type FROM `biblio_position` \
        WHERE item_type='static' AND id_app=%s AND `row`=%s ORDER BY `position`", (app_id, numrow))
    return cursor.fetchall()

def statsBooks(app_id, numrow):
    """Get books quantity by row for module"""
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bp.`row`, count(bb.`id`) as nbbooks FROM biblio_book bb \
        inner join biblio_position bp on bp.id_item=bb.id and bp.item_type='book' \
        inner join biblio_app app on bp.id_app=app.id where app.id=%s and bp.`row`=%s", (app_id, numrow))
    return cursor.fetchone()

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