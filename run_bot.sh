#!/bin/bash

while true
do
  echo "Bot starting at $(date)"
  bash /home/autolig1/site/Autoliga_Botfile/start_bot.sh

  echo "Bot crashed at $(date). Restarting..."
  sleep 5
done