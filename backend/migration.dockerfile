# Use the official Python base image
FROM --platform=linux/amd64 python:3.11.5-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["alembic", "upgrade", "head"]