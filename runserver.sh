#!/bin/bash

./manage.py initialize_db
supervisorctl start after:*
