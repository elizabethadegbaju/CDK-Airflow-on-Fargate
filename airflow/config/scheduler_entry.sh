#!/usr/bin/env bash

# This script is used to start the scheduler in a docker container
set -Eeuxo pipefail
sleep 30
airflow scheduler
