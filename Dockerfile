FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

ARG uid=1001

WORKDIR /app

COPY . /app
COPY ./.env.sample /app/.env

RUN pip3 install --upgrade pip
RUN pip install -r requirements.txt

RUN mkdir /.paddlex

RUN useradd bibliobus --home /app --uid ${uid} 

RUN chown bibliobus:bibliobus /app

USER bibliobus

EXPOSE 8000

ENTRYPOINT ["/app/boot.sh"]