import datetime
import os
import re
from typing import Any, Dict

from minerva.directory_manager.base import (ROOT_DIR_PATH, DirectoryBase,
                                            DirectoryCreator)


class EvernoteDirectory(DirectoryBase):
    ''' Directory for all the Evernote extractor artifacts. '''
    
    def get_base(self) -> str:
        return 'evernote_data'

    def get_structure(self) -> dict[str, any]:
        return {
            'metadata': {},
            'log': {},
            'export': {},
            'analysis': {},
        }

    def get_metadata_dir(self) -> str:
        full_path = self.get_full_path('metadata')
        return full_path
    
    def get_log_dir(self) -> str:
        full_path = self.get_full_path('log')
        return full_path
    
    def get_export_dir(self) -> str:
        full_path = self.get_full_path('export')
        DirectoryCreator.create_directory(full_path)
        return full_path
    
    def get_analysis_dir(self) -> str:
        full_path = self.get_full_path('analysis')
        DirectoryCreator.create_directory(full_path)
        return full_path


class YoutubeDirectory(DirectoryBase):
    ''' Directory for all the YouTube downloader artifacts. '''
    
    def get_base(self) -> str:
        return 'youtube_data'

    def get_structure(self) -> dict[str, any]:
        return {
            'metadata': {},
            'log': {},
            'downloads': {},
            'analysis': {},
        }

    def get_metadata_dir(self) -> str:
        full_path = self.get_full_path('metadata')
        return full_path
    
    def get_log_dir(self) -> str:
        full_path = self.get_full_path('log')
        return full_path
    
    def get_downloads_dir(self) -> str:
        full_path = self.get_full_path('downloads')
        DirectoryCreator.create_directory(full_path)
        return full_path
    
    def get_analysis_dir(self) -> str:
        full_path = self.get_full_path('analysis')
        DirectoryCreator.create_directory(full_path)
        return full_path
    

class TwitterDirectory(DirectoryBase):
    ''' Directory for all the Twitter downloader artifacts. '''
    
    def get_base(self) -> str:
        return 'twitter_data'
    
    def get_structure(self) -> dict[str, any]:
        return {
            'tweets': {},  
        }
    
    def get_tweets_dir(self) -> str:
        full_path = self.get_full_path('tweets')
        DirectoryCreator.create_directory(full_path)
        return full_path
    
    def get_twitter_dir(self) -> str:
        """Alias for get_tweets_dir for backward compatibility"""
        return self.get_tweets_dir()
