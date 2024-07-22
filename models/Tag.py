from fastapi import Path
from typing import Union, Annotated, List
from pydantic import BaseModel, Field
from db import getMyDB
from models import Book, Position
import tools

class Tag(BaseModel):
    id: Annotated[Union[int, None], Path(title="Tag Id")] = Field(examples=["1"])
    tag: Annotated[Union[str, None], Path(title="Tag label")] = Field(examples=["Auster Paul, Biographies"])
    nbnode: Annotated[Union[int, None], Path(title="Nb items related")] = Field(examples=["10"])
    url: Annotated[Union[str, None], Path(title="Url for tag locations")] = Field(examples=["/requests/tag/1"])
    hasRequest: Annotated[Union[int, None], Path(title="If tag have items requested")] = Field(default=0, examples=["5"])
    color: Annotated[Union[str, None], Path(title="Leds Color RGB")] = Field(default=None, examples=["0,86,125"])
    red: Annotated[Union[str, None], Path(title="Red Color value")] = Field(default=None, examples=["0"])
    green: Annotated[Union[str, None], Path(title="Green Color value")] = Field(default=None, examples=["86"])
    blue: Annotated[Union[str, None], Path(title="Blue Color value")] = Field(default=None, examples=["125"])

class TagElementAuthor(BaseModel):
    initial: Annotated[Union[str, None], Path(title="Author's name initial")] = Field(examples=["a"])
    items: List[Tag]

class TagListAuthors(BaseModel):
    list_title: Annotated[Union[str, None], Path(title="Bookshelf name")] = Field(examples=["Biblio Demo"])
    elements: List[TagElementAuthor]

class TagListCategories(BaseModel):
    list_title: Annotated[Union[str, None], Path(title="Bookshelf name")] = Field(examples=["Biblio Demo"])
    elements: List[Tag]

class TagBooksListElements(BaseModel):
    book: Book.Book
    address: Position.Position
    color: Annotated[Union[str, None], Path(title="Leds Color RGB")] = Field(default=None, examples=["0,86,125"])

class TagBooksList(BaseModel):
    list_title: Annotated[Union[str, None], Path(title="Tag name")] = Field(examples=["Auster Paul"])
    elements: List[TagBooksListElements]

def setTagsBook(book, user_id, app_id, tags = None):
    # manage tags + taxonomy
    # author tags
    authorTagids = []
    authors = [book['author']]
    if len(authors) > 0:
        authorTags = tools.getLastnameFirstname(authors)
        authorTagids = saveTags(authorTags,'Authors')
    if len(authorTagids) > 0:
        saveTagNode(book, authorTagids)
    # categories
    catTagIds = []
    if tags is not None :  
        cleanTagForNode(book['id'], 1) #clean tags categories  before update
        catTagIds = saveTags(tags.split(','),'Categories')
    if len(catTagIds) > 0:
        saveTagNode(book, catTagIds)
        saveTagUser(user_id, catTagIds)

def saveTagNode(node, tagIds):
    mydb = getMyDB()
    cursor = mydb.cursor()
    for tag in tagIds:
        cursor.execute("INSERT INTO biblio_tag_node (`node_type`, `id_node`, `id_tag`) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id_tag=%s", \
            ('book', node['id'], tag['id'], tag['id']))
    mydb.commit()

def saveTags(tags, taxonomy_label):
    tag_ids = []
    taxonomy = getIdTaxonomy(taxonomy_label)
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    for tag in tags:
        hasTag = getTag(tag)
        if hasTag is None:
          cursor.execute("INSERT INTO biblio_tags (`tag`, `id_taxonomy`) VALUES (%s, %s)", (tag, taxonomy['id']))
          mydb.commit()
          cursor.execute("SELECT LAST_INSERT_ID() as id")
          row = cursor.fetchone()
          tag_ids.append(row)
        else:
          tag_ids.append(hasTag)
    return tag_ids

def saveTagUser(user_id, tagIds):
    mydb = getMyDB()
    cursor = mydb.cursor()
    for tag in tagIds:
        cursor.execute("INSERT INTO biblio_tag_user (`id_user`, `id_tag`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE id_tag=%s", \
            (user_id, tag['id'], tag['id']))
    mydb.commit()

def getTag(tag):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT id, tag, color FROM biblio_tags WHERE tag=%s", [tag])
    return cursor.fetchone()

def getTagById(tag_id, user_id):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT bt.id, bt.tag, btu.color, bt.id_taxonomy FROM biblio_tags bt \
        LEFT JOIN biblio_tag_user btu ON bt.id = btu.id_tag and btu.id_user=%s \
        WHERE id=%s", (user_id, tag_id))
    return cursor.fetchone()

def getBooksForTag(id_tag, id_app):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT id_node FROM biblio_tag_node btn \
        INNER JOIN biblio_tags bt ON bt.id = btn.id_tag \
        INNER JOIN biblio_book bb ON btn.id_node = bb.id \
        WHERE btn.id_tag=%s and btn.node_type='book' and bb.id_app=%s", (id_tag, id_app))
    return cursor.fetchall()

def getIdTaxonomy(label):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT id, label FROM biblio_taxonomy WHERE label=%s", [label])
    return cursor.fetchone()
  
def cleanTagForNode(id_node, id_taxonomy):
    mydb = getMyDB()
    cursor = mydb.cursor()
    cursor.execute("DELETE tn.* FROM biblio_tag_node tn LEFT JOIN biblio_tags t ON tn.id_tag = t.id \
      WHERE tn.id_node=%s and t.id_taxonomy=%s and tn.node_type='book'", (id_node, id_taxonomy))
    mydb.commit()

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