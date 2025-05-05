import os
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Admin credentials
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')

# Hashed password for the admin user
users = {
    ADMIN_USER: bcrypt.hashpw(ADMIN_PASS.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
}