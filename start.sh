#!/bin/bash
gunicorn app.server:current_app --bind localhost:8000 --worker-class aiohttp.GunicornWebWorker --workers 4