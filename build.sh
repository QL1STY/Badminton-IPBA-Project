#!/usr/bin/env bash
set -o errexit


pip install -r requirements.txt

python run_migrations.py