from typing import Optional

from src.core.config.config import Config


def create_config(postscript_for_paths: Optional[str] = '') -> Config:
    return Config(postscript_for_paths=postscript_for_paths)