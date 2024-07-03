from config import settings
import mysql.connector

def getMyDB():
	try:
		mydb = mysql.connector.connect(
		  host=settings.db_host,
		  user=settings.db_user,
		  password=settings.db_password,
		  database=settings.db_name
		)
	except mysql.connector.Error as err:
		print(err)
		mydb.reconnect()
	else:
	    return mydb