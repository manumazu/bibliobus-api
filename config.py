import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    # load vars from .env file
    load_dotenv()
    db_host: str = os.getenv('DB_HOST')
    db_user: str = os.getenv('DB_USER')
    db_password: str = os.getenv('DB_PASSWORD')
    db_name: str = os.getenv('DB_NAME')
    secret_key: str = os.getenv('SECRET_KEY')
    secret_key_access_token: str = os.getenv('SECRET_KEY_ACCESS_TOKEN')
    google_book_api_key: str = os.getenv('GOOGLE_BOOK_API_KEY')

settings = Settings()