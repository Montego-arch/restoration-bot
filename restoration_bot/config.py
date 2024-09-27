import toml

def load_config(config_path):
    try:
        return toml.load(config_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")


