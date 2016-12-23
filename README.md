# Auth/Proxy

An oAuth/proxy layer for FHIR servers. It uses [Flask-OAuthlib](https://flask-oauthlib.readthedocs.io/en/latest/) to provide OAuth2 compliant authentication and transparently forwards API requests to a configured FHIR server.

## Installation

```
pip install .
```

## Configuration

auth-proxy checks the environment for:

+ **API_SERVER**: The target FHIR server.

## Running

```
flask run
```
