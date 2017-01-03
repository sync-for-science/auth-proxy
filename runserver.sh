#!/bin/bash

flask initdb
flask load_fixtures
supervisorctl start after:*
