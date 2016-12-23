FROM python:3-onbuild
MAINTAINER Josh Mandel

# Install required packages
RUN apt-get update
RUN apt-get install -y \
    supervisor
RUN apt-get clean

# Set the environment
ENV FLASK_APP /usr/src/app/app.py
ENV API_SERVER http://api:8080/baseDstu2
ENV API_SERVER_NAME 'Mainline Clinic'

WORKDIR /usr/src/app

CMD ["supervisord", "-c", "supervisord.conf"]
