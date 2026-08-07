#!/usr/bin/env bash
# start.sh

echo "Running database migrations"
alembic upgrade head

echo "Starting the server"
# replace "your_python_script.py" with the actual script name that starts your server
python main.py