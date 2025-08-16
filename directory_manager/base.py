import os
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict

'''
Split the pathname path into a pair, (head, tail) where tail is the 
last pathname component and head is everything leading up to that. 

Ex:
If the
MINERVA_DIR_PATH = '/Users/jinchao/AlgoTrading/minerva_base/minerva'

then the
ROOT_DIR = '/Users/jinchao/AlgoTrading/minerva_base'

Note: MINERVA_DIR_PATH always points to the minerva directory where 
this module is located, regardless of the current working directory.
'''
# Check if MINERVA_ROOT_DIR environment variable is set (for development)
# This allows the code to work both when installed via setup.py and in development
MINERVA_ROOT_DIR_ENV = os.environ.get('MINERVA_ROOT_DIR')

if MINERVA_ROOT_DIR_ENV:
    # Use the environment variable if set (for development)
    ROOT_DIR_PATH = MINERVA_ROOT_DIR_ENV
    MINERVA_DIR_PATH = os.path.join(ROOT_DIR_PATH, 'minerva')
else:
    # Fallback to the original behavior if not in development mode
    # Try to detect if we're in a development environment
    current_file_path = os.path.abspath(__file__)
    
    # Check if we're in a typical development structure
    if '/AlgoTrading/minerva_base/minerva/' in current_file_path:
        # Extract the root path from the development structure
        parts = current_file_path.split('/AlgoTrading/minerva_base/minerva/')
        ROOT_DIR_PATH = parts[0] + '/AlgoTrading/minerva_base'
        MINERVA_DIR_PATH = os.path.join(ROOT_DIR_PATH, 'minerva')
    else:
        # Fallback to original calculation (for compatibility)
        MINERVA_DIR_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ROOT_DIR_PATH = os.path.split(MINERVA_DIR_PATH)[0]  


class DirectoryCreator:
    @staticmethod
    def create_directory(path: str) -> None:
        if not os.path.exists(path):
            print(f'Creating directory: {path}')
            os.makedirs(path)
        else:
            print(f'Directory already exists: {path}')

    @classmethod
    def setup_directories(cls, root_path: str, structure: Dict[str, Any]) -> None:
        for key, value in structure.items():
            dir_path = os.path.join(root_path, key)
            cls.create_directory(dir_path)
            if isinstance(value, dict) and value:
                cls.setup_directories(dir_path, value)


# ==============================================================================

# Directory Base Class

# ==============================================================================

class DirectoryBase(ABC):
    def __init__(self):
        self.base = self.get_base()
        self.structure = self.get_structure()

    @abstractmethod
    def get_base(self) -> str:
        """Return the base directory name."""
        raise NotImplementedError('Child class must implement this method')

    @abstractmethod
    def get_structure(self) -> Dict[str, Any]:
        """Return the directory structure as a nested dictionary."""
        raise NotImplementedError('Child class must implement this method')

    def setup_directories(self, root_path: str = ROOT_DIR_PATH) -> None:
        """Create the directory structure."""
        base_path = os.path.join(root_path, self.base)
        DirectoryCreator.create_directory(base_path)
        DirectoryCreator.setup_directories(base_path, self.structure)

    def get_full_path(self, *path_parts: str, create_if_not_exists: bool = False) -> str:
        """Get the full path for a given subdirectory or file."""
        full_path = os.path.join(ROOT_DIR_PATH, self.base, *path_parts)
        if create_if_not_exists and not os.path.exists(full_path):
            DirectoryCreator.create_directory(full_path)
        return full_path