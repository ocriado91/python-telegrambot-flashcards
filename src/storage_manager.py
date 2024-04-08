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

        # Store selected item
        self.item = ()

        # Create table
        self.conn = sqlite3.connect(database=database,
                                    timeout=timeout)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS items
                            (id INTEGER PRIMARY KEY,
                            inserted_date TEXT,
                            answer TEXT,
                            quiz TEXT,
                            answer_correct_count INTEGER,
                            answer_wrong_count INTEGER,
                            item_type TEXT)''')

        # Add unique constraint to the answer column
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS
                            idx_answer_unique
                            ON items (answer)''')

    def insert_item(self,
                    item_type: str,
                    answer: str,
                    quiz: str) -> None:
        '''
        Add a new item to the database

        Parameters:
            - item_type (str): Type of item (text, photo, audio or video)
            - answer (str): Field that will be shown into a round
            - quiz (str): Field that must be to guessed into a round
        '''
        try:
            now = datetime.strftime(datetime.now(), DATE_FMT)
            self.cursor.execute('''INSERT INTO items (
                                    inserted_date,
                                    answer,
                                    quiz,
                                    answer_correct_count,
                                    answer_wrong_count,
                                    item_type)
                                    VALUES (?, ?, ?, ?, ?, ?)''',
                                    (now, answer, quiz,
                                    0, 0, item_type))
            self.conn.commit()
            logger.info("Successfully store new item %s: %s - %s",
                        item_type, answer, quiz)
        except sqlite3.IntegrityError as exception:
            msg = f"Already a item with answer {answer} has been created."
            raise StorageManagerException(msg) from exception

        except sqlite3.ProgrammingError as exception:
            raise StorageManagerException(
                "Connection to DB is already closed"
            ) from exception

    def _update_db_numeric_field(self,
                                field: str,
                                item_id: int) -> None:
        '''
        Update a numeric field into database

        Parameters
         - field (str): Numeric field to be incremented
         - item_id (int): ID of item to be modified
        '''

        query = f'''UPDATE items
                    set {field} = {field} + 1
                    WHERE id = {item_id}'''
        self.cursor.execute(query)
        self.conn.commit()
        logger.info("Successfully updated %s", field)

    def select_random_item(self) -> str:
        '''
        Extract a random item from database

        Returns:
            - item: The quiz string of randomly selected item
        '''

        # Extract the length of the database
        self.item = self.cursor.execute('''SELECT * FROM items
                                  ORDER BY RANDOM() LIMIT 1''').fetchone()
        self.conn.commit()

        if not self.item:
            raise StorageManagerException("None item detected into database")
        logger.info("Result: %s", self.item)

        quiz = self.item[3]
        item_type = self.item[6]
        return quiz, item_type

    def check_quiz_item(self,
                        attempt: str) -> bool:
        '''
        Check if attempt string is into database

        Parameters
            - attempt (str): String to check into database

        Returns
            -  bool: True is attempt string is into database. False otherwise
        '''

        query = '''SELECT EXISTS(SELECT 1 FROM items WHERE answer = ?)'''
        is_matched = self.cursor.execute(query, (attempt,)).fetchone()[0]

        # Update attempt counters
        field = "answer_wrong_count"
        if is_matched:
            field = "answer_correct_count"
        self._update_db_numeric_field(field, self.item[0])

        return is_matched

    def close_connection(self):
        '''
        Close connection to database
        '''

        self.cursor.close()
        self.conn.close()
