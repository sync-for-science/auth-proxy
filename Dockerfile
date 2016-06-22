FROM python:3-onbuild
MAINTAINER Josh Mandel

# Install required packages
RUN apt-get update
RUN apt-get install -y \
    supervisor
RUN apt-get clean

# Init the db
ENV FLASK_APP /usr/src/app/runserver.py
ENV API_SERVER http://api:8080/baseDstu2

WORKDIR /usr/src/app

CMD supervisord -c supervisord.conf
