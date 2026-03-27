import os
import sys

# путь к проекту
sys.path.insert(0, '/home/autolig1/site')

# настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# запуск Django
from myproject.wsgi import application

