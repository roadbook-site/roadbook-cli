import json
import yaml
from ..core.config import load_config, load_user_config, save_user_config, load_project_config, save_project_config, DEFAULT_CONFIG, PROJECT_CONFIG_FILE, USER_CONFIG_FILE
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
    if PROJECT_CONFIG_FILE.exists():
        print_info(f" - Includes project config: {PROJECT_CONFIG_FILE}")
    print_info(f" - Includes global config: {USER_CONFIG_FILE}\n")
    print(yaml.dump(config, default_flow_style=False))
    print_info("\nTip: Run `roadbook doctor` to verify if the current configuration is valid.")

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
    """Set a configuration value."""
    is_global = getattr(args, 'global_config', False)
    
    # If -g is not passed, check if we are in a project
    if is_global:
        target = "global"
    elif PROJECT_CONFIG_FILE.parent.exists() or PROJECT_CONFIG_FILE.exists():
        target = "project"
    else:
        target = "global"

    if target == "project":
        config_data = load_project_config()
        if not config_data:
            config_data = {}

        if _set_nested_value(config_data, args.key, args.value):
            save_project_config(config_data)
            print_success(f"Updated '{args.key}' to '{args.value}' in project config.")
            print_info(f"File updated: {PROJECT_CONFIG_FILE}")
        else:
            print_error(f"Failed to set '{args.key}'. Path conflict or invalid structure.")
    else:
        config_data = load_user_config()
        if not config_data:
            config_data = {}

        if _set_nested_value(config_data, args.key, args.value):
            save_user_config(config_data)
            print_success(f"Updated '{args.key}' to '{args.value}' in global config.")
            print_info(f"File updated: {USER_CONFIG_FILE}")
        else:
            print_error(f"Failed to set '{args.key}'. Path conflict or invalid structure.")
