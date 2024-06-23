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