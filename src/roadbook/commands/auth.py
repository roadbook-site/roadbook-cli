from ..core.api import APIClient
from ..core.config import set_api_key, get_server_url
from ..utils.output import print_info, print_success, print_error

def login(args):
    server_url = get_server_url()
    print_info(f"Please get your API key from {server_url}/settings/api-keys")
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print_error("API Key cannot be empty.")
        return

    try:
        set_api_key(api_key)
        # Verify the key (optional, if there is an endpoint like GET /users/me)
        client = APIClient()
        # You could verify via client.get_user() if it exists
        client.get_me()
        print_success("Logged in successfully with API Key!")
    except Exception as e:
        print_error(f"Login failed: {e}")
