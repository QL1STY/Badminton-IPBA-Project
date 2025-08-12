#!/usr/bin/env bash
set -o errexit


pip install -r requirements.txt

python run_migrations.py#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run database migrations
flask db upgrade

# Create the admin user (if not exists)
flask init-admin