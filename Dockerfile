FROM python:slim

ARG uid=1001

WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip install fastapi uvicorn
RUN pip install pydantic-settings
RUN pip install mysql-connector-python
RUN pip install PyJWT
RUN pip install requests

RUN useradd bibliobus --home /app --uid ${uid} 

COPY . /app
COPY ./.env.sample /app/.env

RUN chown bibliobus:bibliobus /app

USER bibliobus

EXPOSE 8000

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]