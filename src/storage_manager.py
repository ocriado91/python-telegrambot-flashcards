#!/usr/bin/env python3
'''
StorageManager definition
'''
import sqlite3

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
                            period_type INT,
                            answer_correct_count INTEGER,
                            answer_wrong_count INTEGER,
                            last_attempt_date TEXT,
                            item_type TEXT)''')

        # Add unique constraint to the target column
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS
                            idx_target_unique
                            ON items (target)''')

    def close_connection(self):
        '''
        Close connection to database
        '''

        self.cursor.close()
        self.conn.close()
