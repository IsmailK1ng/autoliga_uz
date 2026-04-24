#!/bin/bash
cd /home/autolig1/site || exit 1

# Убиваем старый процесс если есть
pkill -f "/home/autolig1/site/Autoliga_Botfile/run_bot.py" 2>/dev/null
sleep 2

# Запускаем
nohup /home/autolig1/virtualenv/site/3.13/bin/python /home/autolig1/site/Autoliga_Botfile/run_bot.py >> /home/autolig1/site/logs/bot.log 2>&1 &
echo $! > /home/autolig1/tmp/bot.pid
echo "Bot started with PID $(cat /home/autolig1/tmp/bot.pid)"
