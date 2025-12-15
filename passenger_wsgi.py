import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/public_html/keem_driving_school'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['PYTHON_EGG_CACHE'] = '/home/yourusername/.python-eggs'

# Import Flask application
from keem.app11 import app as application