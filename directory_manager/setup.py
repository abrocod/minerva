import os

from minerva.directory_manager.base import ROOT_DIR_PATH, DirectoryBase
from minerva.directory_manager.directory_definition import (
    EvernoteDirectory,
    YoutubeDirectory,
    TwitterDirectory
)


class DirectoryStructureBuilder:
    @staticmethod
    def setup_all_directories():
        directories: list[DirectoryBase] = [
            EvernoteDirectory(),
            YoutubeDirectory(),
            TwitterDirectory(),
        ]

        for directory in directories:
            directory.setup_directories(ROOT_DIR_PATH)

    @staticmethod
    def print_directory_structure(start_path=ROOT_DIR_PATH):
        for root, dirs, files in os.walk(start_path):
            level = root.replace(start_path, '').count(os.sep)
            indent = ' ' * 4 * level
            print(f"{indent}{os.path.basename(root)}/")

if __name__ == "__main__":
    DirectoryStructureBuilder.setup_all_directories()
    print("Directory structure setup completed.")
    print("\nDirectory structure:")
    DirectoryStructureBuilder.print_directory_structure()