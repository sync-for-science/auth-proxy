FROM python:3
MAINTAINER Josh Mandel

# Install required packages
RUN apt-get update
RUN apt-get install -y \
    supervisor
RUN apt-get clean

# Copy the codebase
COPY . /auth-proxy
WORKDIR /auth-proxy

# Install requirements
RUN pip install -r requirements.txt

# Init the db
ENV FLASK_APP /auth-proxy/runserver.py
ENV API_SERVER http://api:8080/baseDstu2

CMD supervisord -c /auth-proxy/supervisord.conf
