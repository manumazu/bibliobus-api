FROM python:3.13-slim

ARG uid=1001

WORKDIR /app

COPY . /app
COPY ./.env.sample /app/.env

RUN pip3 install --upgrade pip
RUN pip install -r requirements.txt

RUN useradd bibliobus --home /app --uid ${uid} 

RUN chown bibliobus:bibliobus /app

USER bibliobus

EXPOSE 8000

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]