FROM python:slim

ENV DB_HOST=172.17.0.1

COPY . /app

WORKDIR /app
RUN python -m pip install --upgrade pip
RUN pip install fastapi
RUN pip install pydantic-settings
RUN pip install mysql-connector-python
RUN pip install PyJWT

#RUN chmod +x /app/boot.sh
#RUN ls -l /app/boot.sh

EXPOSE 8000

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]