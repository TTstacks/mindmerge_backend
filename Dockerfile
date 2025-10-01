FROM python:3.12-slim-bullseye AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
apt-get install -y libpq-dev gcc

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


RUN python -m pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.12-slim-bullseye

RUN apt-get update && \
apt-get install -y libpq-dev

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
COPY . .