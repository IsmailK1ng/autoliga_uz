#!/bin/bash
cd /home/autolig1/site/Autoliga_Botfile
source /home/autolig1/virtualenv/site/3.13/bin/activate

# Убиваем старый процесс если есть
pkill -f "python bot.py" 2>/dev/null
sleep 2

# Запускаем
nohup python bot.py >> /home/autolig1/logs/bot.log 2>&1 &
echo $! > /home/autolig1/tmp/bot.pid
echo "Bot started with PID $(cat /home/autolig1/tmp/bot.pid)"
