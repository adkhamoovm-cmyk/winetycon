#!/bin/bash
echo "Installing pip..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3

echo "Installing requirements..."
python3 -m pip install -r bot/requirements.txt

echo "Killing any previous bot instances..."
pkill -f "python3 bot/main.py" || true

echo "Starting Telegram Bot..."
PYTHONPATH=. python3 bot/main.py
