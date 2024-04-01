#!/usr/bin/env python3
'''
StorageManager definition
'''

from datetime import datetime
import logging
import sqlite3

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATE_FMT = '%Y/%m/%dT%H:%M:%S'

class StorageManagerException(Exception):
    '''
    Raised when there is a integrity error into database
    '''
    def __init__(self,
                 message):
        super().__init__(message)


class StorageManager:
    '''
    Class to manage all databases
    '''
    def __init__(self,
                 database: str = 'flashcard.db',
                 timeout: int = 20) -> None:
        # Create table
        self.conn = sqlite3.connect(database=database,
                                    timeout=timeout)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS items
                            (id INTEGER PRIMARY KEY,
                            inserted_date TEXT,
                            target TEXT,
                            source TEXT,
                            answer_correct_count INTEGER,
                            answer_wrong_count INTEGER,
                            item_type TEXT)''')

        # Add unique constraint to the target column
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS
                            idx_target_unique
                            ON items (target)''')

    def insert_item(self,
                    item_type: str,
                    target: str,
                    source: str) -> None:
        '''
        Add a new item to the database

        Parameters:
            - item_type (str): Type of item (text, photo, audio or video)
            - target (str): Field that will be shown into a round
            - source (str): Field that must be to guessed into a round
        '''
        try:
            now = datetime.strftime(datetime.now(), DATE_FMT)
            self.cursor.execute('''INSERT INTO items (
                                    inserted_date,
                                    target,
                                    source,
                                    answer_correct_count,
                                    answer_wrong_count,
                                    item_type)
                                    VALUES (?, ?, ?, ?, ?, ?)''',
                                    (now, target, source,
                                    0, 0, item_type))
            self.conn.commit()
            logger.info("Successfully store new item %s: %s - %s",
                        item_type, target, source)
        except sqlite3.IntegrityError as exception:
            raise StorageManagerException(
                f"Items {target} - {source} already stored") from exception

    def close_connection(self):
        '''
        Close connection to database
        '''

        self.cursor.close()
        self.conn.close()
