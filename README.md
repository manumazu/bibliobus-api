# bibliobus-api
Rest API for bibliobus project using FastAPI
This project use a [FastAPI](https://fastapi.tiangolo.com/) instance
A demo of this project is running at https://api.bibliob.us/docs

## Install
```
python3 -m venv venv
. venv/bin/activate
pip install fastapi
pip install pydantic-settings
pip install mysql-connector-python
pip install PyJWT
pip install requests
```

## Start
```
. venv/bin/activate
uvicorn main:app --reload
```