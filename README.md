# bibliobus-api
Rest API for bibliobus project using FastAPI

## Install
```
python3 -m venv venv
. venv/bin/activate
pip install fastapi
pip install pydantic-settings
pip install mysql-connector-python
pip install PyJWT
```

## Start
```
. venv/bin/activate
uvicorn main:app --reload
```