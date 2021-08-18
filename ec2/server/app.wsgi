import sys
sys.path.insert(0, '/var/www/html/app')

# activating virtual environment for apache
activate_this = '/home/ec2-user/.local/share/virtualenvs/app-z0unTUMf/bin/activate_this.py'
with open(activate_this) as file:
    exec(file.read(), dict(__file__=activate_this))

from app import app as application
