#!/bin/sh
set -e

if [ "$1" = "serve" ]; then
    # Start your inference server
    exec poetry run python unified_app.py serve
else
    # Execute the passed command
    exec "$@"
fi

