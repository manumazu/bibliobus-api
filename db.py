from config import settings
import mysql.connector

mydb = mysql.connector.connect(
	  host=settings.db_host,
	  user=settings.db_user,
	  password=settings.db_password,
	  database=settings.db_name
	)