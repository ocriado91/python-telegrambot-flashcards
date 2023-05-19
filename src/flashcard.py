#!/usr/bin/env python3
'''
A TelegramBot to learn new words
'''

from datetime import datetime

import logging
import random
import sqlite3
import sys
import time
import tomli

from telegrambot import TelegramBot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)

DATE_FMT = '%Y/%m/%dT%H:%M:%S'


class FlashCardBot:
    '''
    FlashCard class object
    '''

    def __init__(self,
                 config: dict,
                 database: str = 'flashcard.db',
                 max_attempts: int = 3) -> None:
        '''
        Constructor of FlashCardBot class
        '''

        self.telegrambot = TelegramBot(config['Telegram']['API_KEY'])
        self.pending_item = False
        self.target = []
        self.max_attemps = max_attempts
        self.attempt = 0

        # Create table
        self.conn = sqlite3.connect(database)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS items
                            (id INTEGER PRIMARY KEY,
                            inserted_date TEXT,
                            target TEXT,
                            source TEXT,
                            period_type TEXT,
                            answer_correct_count INTEGER,
                            answer_wrong_count INTEGER,
                            last_attempt_date TEXT)''')

        # Add unique constraint to the target column
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_target_unique
                            ON items (target)''')

    def polling(self,
                sleep_time: int = 1):  # pragma: no cover
        '''
        Check incoming message from TelegramBot API
        through  a polling mechanism
        '''

        last_message_id = -1
        while True:
            message_id = self.telegrambot.extract_message_id()

            # Discard first iteration until new incoming message
            if last_message_id == -1:
                last_message_id = message_id

            # Check if new message is available and
            # if incoming message is different from previous one
            if message_id:
                if message_id != last_message_id:
                    message = self.telegrambot.read_message()
                    logger.info('Received message = %s', message)
                    self.process_message(message)
                    last_message_id = message_id

            time.sleep(sleep_time)

    def process_message(self,
                        message: str,
                        delimiter: str = ':'):
        '''
        Extract action from incoming message being
        action defined into <ACTION>: <ITEM> format
        '''

        # Check if there is a pending to answer item,
        # if not, process command
        if self.pending_item is True:
            self.process_answer(message)
        else:
            # By default, the incoming message is the command
            # without related items
            action = message
            items = None

            # If a delimiter is detected, strip message
            # to extract both fields
            if delimiter in message:
                action, items = message.split(delimiter)

            self.process_action(action, items)

    def process_action(self,
                       action: str,
                       item: str):
        '''
        Process incoming action
        '''

        # Apply desired action
        if action == 'new':
            logger.info('Adding item')
            self.action_new_item(item)
        elif action == 'remove':
            logger.info('Removing item')
            self.action_remove_item(item)
        elif action == 'show':
            logger.info('Showing item')
            self.action_show_item()
        else:
            warning_message = f'Unknown action {action}'
            self.telegrambot.send_message(warning_message)
            logger.warning(warning_message)

    def action_new_item(self,
                        text: str,
                        delimiter: str = '-'):
        '''
        Save new item into database
        '''

        try:
            now = datetime.strftime(datetime.now(), DATE_FMT)
            word1, word2 = text.split(delimiter)
            word1 = word1.strip()
            word2 = word2.strip()

            self.cursor.execute('''INSERT INTO items (inserted_date, target,
                                source, period_type, answer_correct_count,
                                answer_wrong_count, last_attempt_date)
                                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                (now, word1, word2, "Daily", 0, 0, now))
            self.conn.commit()
            msg = f'Successfully added new item {word1} - {word2}'
            self.telegrambot.send_message(msg)
            logging.info(msg)
        except ValueError:
            warning_message = f'Invalid item {text}'
            self.telegrambot.send_message(warning_message)
            logger.warning(warning_message)
        except sqlite3.IntegrityError:
            warning_message = f'Item with target "{word1}" already exists'
            self.telegrambot.send_message(warning_message)
            logger.warning(warning_message)

    def action_remove_item(self,
                           text: str,
                           delimiter: str = '-'):
        '''
        Remove item from database
        '''

        # Pre-process item
        word1, word2 = text.split(delimiter)
        word1 = word1.strip()
        word2 = word2.strip()

        logger.info('Trying to remove %s', word1)

        # Check if item is into database
        self.cursor.execute('''SELECT COUNT(*) FROM items where target=?''',
                            (word1,))
        result = self.cursor.fetchone()
        if result[0] > 0:
            self.cursor.execute("DELETE FROM items WHERE target=?", (word1,))
            self.conn.commit()
            msg = 'Successfully removed items'
            self.telegrambot.send_message(msg)
            logger.info(msg)
        else:
            warning_message = f'Item {word1} - {word2} not found in database'
            self.telegrambot.send_message(warning_message)
            logger.warning(warning_message)

    def action_show_item(self):
        '''
        Extract randomly item from database
        '''

        self.cursor.execute('SELECT * from items')
        rows = self.cursor.fetchall()
        if rows:
            logger.info(rows)
            self.target = random.choice(rows)
            logger.info('Selected row %s', self.target)
            logger.info('Send word %s to bot', self.target)
            self.telegrambot.send_message(self.target[2])
            now = datetime.strftime(datetime.now(), DATE_FMT)
            self.update_db_field('last_attempt_date', now)
            self.pending_item = True
        else:
            warning_message = 'No items found in database'
            self.telegrambot.send_message(warning_message)
            logger.warning(warning_message)

    def process_answer(self,
                       message: str):
        '''
        Check if answer sent via Telegram is correct
        '''
        if message == self.target[3]:
            msg = 'OK!'
            self.telegrambot.send_message(msg)
            logger.info(msg)
            self.update_db_numeric_field("answer_correct_count")
            self.reset_answer()
        else:
            self.attempt += 1
            msg = f'ERROR - Current attempt {self.attempt}'
            self.telegrambot.send_message(msg)
            logger.info(msg)
            self.update_db_numeric_field("answer_wrong_count")
            if self.attempt >= self.max_attemps:
                self.reset_answer()
                msg = f'Reached max. number of attemps ({self.max_attemps})'
                self.telegrambot.send_message(msg)
                logger.error(msg)

    def reset_answer(self):
        '''
        Reset answer attributes
        '''
        self.target = []
        self.pending_item = False
        self.attempt = 0

    def update_db_field(self,
                        field: str,
                        value: str):
        '''
        Update a numeric field into database
        '''

        logger.info(self.target)
        sql_query = f'''UPDATE items
                        SET {field} = '{value}'
                        WHERE target='{self.target[2]}';'''
        self.cursor.execute(sql_query)
        self.conn.commit()
        logger.info('Successfully updated answer_correct_count')

    def update_db_numeric_field(self,
                                field: str):
        '''
        Update a numeric field into database
        '''

        logger.info(self.target)
        sql_query = f'''UPDATE items
                        SET {field} = {field} + 1
                        WHERE target='{self.target[2]}';'''
        self.cursor.execute(sql_query)
        self.conn.commit()
        logger.info('Successfully updated answer_correct_count')

    def close_connection(self):  # pragma: no cover
        '''
        Close connection to database
        '''
        self.cursor.close()
        self.conn.close()


def read_config(configfile: str) -> dict:
    '''
    Read TOM configuration file and extract fields
    '''

    with open(configfile, 'rb') as config_reader:
        config = tomli.load(config_reader)

    return config


def main():  # pragma: no cover
    '''
    Main function
    '''

    # Read configuration file
    config = read_config(sys.argv[1])

    # Built FlashCard Bot object
    bot = FlashCardBot(config)

    try:
        # Start polling mechanism
        bot.polling()
    except KeyboardInterrupt:
        bot.close_connection()


if __name__ == '__main__':  # pragma: no cover
    main()
