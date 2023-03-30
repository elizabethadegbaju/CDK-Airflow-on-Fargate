#!/usr/bin/env bash

# This script is used to start the webserver in a docker container
set -Eeuxo pipefail
airflow db init
sleep 5
airflow users create \
  --username admin \
  --firstname admin \
  --lastname admin \
  --role Admin \
  --email "${ADMIN_EMAIL}" \
  --password "${ADMIN_PASSWORD}"
sleep 5
airflow webserver
