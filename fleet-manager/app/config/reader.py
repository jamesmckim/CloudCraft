import yaml
from importlib import resources

def load_yaml(filename):
    """
    Safely loads a YAML file and returns its parsed contents.
    Returns an empty dictionary if the file is missing or invalid.
    """
    try:
        
        yaml_text = resources.files(__package__).joinpath(filename).read_text()
        
        return yaml.safe_load(yaml_text) or {}
        
    except FileNotFoundError:
        print(f"Critical Error: Could not find {filename}")
        return {}
    except yaml.YAMLError as exc:
        print(f"Critical Error: Invalid YAML format in {filename}\n{exc}")
        return {}

# These variables are exposed and will be evaluated when the module is imported
GAME_TEMPLATES = load_yaml('templates.yaml')
SETTINGS = load_yaml('settings.yaml')