#!/bin/bash

flask initdb
supervisorctl start after:*
