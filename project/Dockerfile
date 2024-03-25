# pull official base image
FROM python:3.11.2-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
RUN pip install --upgrade pip setuptools
RUN apt-get update -y
RUN apt-get install -y iputils-ping
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .