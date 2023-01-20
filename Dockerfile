# syntax=docker/dockerfile:1

FROM python:lastest
EXPOSE 5000

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
CMD [ "python3", "main.py", "0.0.0.0", "5000"]
