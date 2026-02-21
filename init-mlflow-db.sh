#!/bin/sh
set -e
# Create a separate database for MLflow so it doesn't conflict with the app's "experiments" tables.
psql -v ON_ERROR_STOP=1 --username "experiments" --dbname "experiments" -c "CREATE DATABASE mlflow;"
