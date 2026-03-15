from getpass import getpass
from ..core.api import APIClient
from ..core.config import set_token
from ..utils.output import print_info, print_success, print_error

def login(args):
    print_info("Logging in to Roadbook Server...")
    username = input("Username: ")
    password = getpass("Password: ")
    
    client = APIClient()
    try:
        token = client.login(username, password)
        set_token(token)
        print_success("Login successful!")
    except Exception as e:
        print_error(f"Login failed: {e}")
