import json
import yaml
from ..core.config import load_config, load_user_config, save_user_config, DEFAULT_CONFIG
from ..utils.output import print_info, print_error, print_success

def _get_nested_value(data, path):
    """Get value from nested dictionary using dot notation."""
    keys = path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current

def _set_nested_value(data, path, value):
    """Set value in nested dictionary using dot notation.
    Creates nested dictionaries if they don't exist.
    """
    keys = path.split('.')
    current = data
    for i, key in enumerate(keys[:-1]):
        if key not in current:
            current[key] = {}
        
        # Check if the current path element is a dict before proceeding
        if not isinstance(current[key], dict):
             return False
        current = current[key]
    
    last_key = keys[-1]
    
    # Simple type inference
    typed_value = value
    if isinstance(value, str):
        if value.lower() in ('true', 'yes', 'on'):
            typed_value = True
        elif value.lower() in ('false', 'no', 'off'):
            typed_value = False
        else:
            try:
                typed_value = int(value)
            except ValueError:
                try:
                    typed_value = float(value)
                except ValueError:
                    typed_value = value
            
    current[last_key] = typed_value
    return True

def config_list(args):
    """List all configurations."""
    config = load_config()
    print_info("Current Configuration (Merged):")
    print(yaml.dump(config, default_flow_style=False))

def config_get(args):
    """Get a configuration value."""
    config = load_config()
    value = _get_nested_value(config, args.key)
    if value is not None:
        if isinstance(value, (dict, list)):
            print(json.dumps(value, indent=2))
        else:
            print(value)
    else:
        print_error(f"Key '{args.key}' not found.")

def config_set(args):
    """Set a user configuration value."""
    user_config = load_user_config()
    
    # Initialize with default structure if empty
    if not user_config:
        user_config = {}

    if _set_nested_value(user_config, args.key, args.value):
        save_user_config(user_config)
        print_success(f"Updated '{args.key}' to '{args.value}' in user config.")
    else:
        print_error(f"Failed to set '{args.key}'. Path conflict or invalid structure.")
