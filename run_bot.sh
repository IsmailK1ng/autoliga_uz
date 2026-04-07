#!/bin/bash

if pgrep -f run_bot.py > /dev/null; then
    echo "Bot is already running."
    exit 0
fi

while true
do
    echo "Starting bot via run_bot.py at $(date)"
    python /home/autolig1/site/Autoliga_Botfile/run_bot.py
    echo "Bot crashed at $(date). Restarting in 5 seconds..."
    sleep 5
done
