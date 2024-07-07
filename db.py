from config import settings
import mysql.connector

def getMyDB():
	mydb = mysql.connector.connect(
	  host=settings.db_host,
	  user=settings.db_user,
	  password=settings.db_password,
	  database=settings.db_name
	)
	if mydb and not mydb.is_connected():
		mydb.reconnect()
	return mydb