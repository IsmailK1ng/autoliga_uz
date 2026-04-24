#!/bin/bash

BASE_DIR="/home/autolig1/site"
RUNNER="$BASE_DIR/Autoliga_Botfile/run_bot.py"
PYTHON_BIN="/home/autolig1/virtualenv/site/3.13/bin/python"
LOG_DIR="$BASE_DIR/logs"
BOT_LOG="$LOG_DIR/bot.log"
SUPERVISOR_LOG="$LOG_DIR/bot-supervisor.log"

mkdir -p "$LOG_DIR"

if pgrep -f "$RUNNER" > /dev/null; then
    echo "Bot is already running."
    exit 0
fi

cd "$BASE_DIR" || exit 1

while true
do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting bot via run_bot.py" >> "$SUPERVISOR_LOG"
    "$PYTHON_BIN" "$RUNNER" >> "$BOT_LOG" 2>&1
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot exited with code $EXIT_CODE. Restarting in 5 seconds..." >> "$SUPERVISOR_LOG"
    sleep 5
done
