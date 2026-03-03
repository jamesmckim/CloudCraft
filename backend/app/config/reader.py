import os
import yaml

# Since reader.py is in the same directory as the YAML files,
# we just get the directory of the current file.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_FILE = os.path.join(CURRENT_DIR, 'templates.yaml')
SETTINGS_FILE = os.path.join(CURRENT_DIR, 'settings.yaml')

def load_yaml(file_path):
    """
    Safely loads a YAML file and returns its parsed contents.
    Returns an empty dictionary if the file is missing or invalid.
    """
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        print(f"Critical Error: Could not find {file_path}")
        return {}
    except yaml.YAMLError as exc:
        print(f"Critical Error: Invalid YAML format in {file_path}\n{exc}")
        return {}

# These variables are exposed and will be evaluated when the module is imported
GAME_TEMPLATES = load_yaml(TEMPLATE_FILE)
SETTINGS = load_yaml(SETTINGS_FILE)