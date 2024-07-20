from fastapi import Path
from typing import Union, Annotated, List
from pydantic import BaseModel, Field
from db import getMyDB
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

class shelfLedColum(BaseModel):
    led_column: int
    book: Book

class shelfStats(BaseModel):
    nbbooks: int
    positionRate: int

class shelfElement(BaseModel):
    numshelf: int
    items: List[shelfLedColum] 
    stats: shelfStats

class BookShelf(BaseModel):
    list_title: Annotated[Union[str, None], Path(title="Bookshelf name")] = Field(examples=["Biblio Demo"])
    books: List[shelfElement]


async def getBooksForShelf(numshelf, device, user):
    ''' Get list of books order by positions '''
    shelfs = range(1,device['nb_lines']+1)
    if numshelf:
        shelfs = [numshelf]
    elements = []
    for shelf in shelfs:
        item_list = []
        books = getBooksForRow(device['id'], shelf)
        if books:    
            element = {}
            for row in books:
                book = getBook(row['id'], user['id'])
                book.update({'url':'/books/item/'+str(row['id']), 'borrowed':row['borrowed']})
                requested = getRequestForPosition(device['id'], row['position'], shelf)
                if requested:
                    book.update({'requested': True})
                #print(book)
                item_list.append({'led_column': row['led_column'], 'book': book})
        # get stats elements for shelf
        statBooks = statsBooks(device['id'], shelf)
        statPositions = statsPositions(device['id'], shelf)
        positionRate = 0
        if statPositions['totpos'] != None:
            positionRate = round((statPositions['totpos']/device['nb_cols'])*100)
        stats = {'nbbooks':statBooks['nbbooks'], 'positionRate':positionRate}            
        elements.append({'numshelf': shelf, 'items': item_list, 'stats': stats})
    return elements   

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

def getRequestForPosition(app_id, position, numrow):
    mydb = getMyDB()
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM biblio_request where id_app=%s and `column`=%s and `row`=%s \
    and `action`='add'", (app_id, position, numrow))
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