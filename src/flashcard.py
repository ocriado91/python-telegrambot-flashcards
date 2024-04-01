#!/usr/bin/env python3
'''
A TelegramBot to learn new words
'''

from datetime import datetime
from enum import IntEnum

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

SECONDS_IN_A_DAY = 24 * 60 * 60
SECONDS_IN_A_WEEK = 7 * SECONDS_IN_A_DAY
SECONDS_IN_TWO_WEEKS = 2 * SECONDS_IN_A_WEEK
SECONDS_IN_A_MONTH = 30 * SECONDS_IN_A_DAY  # Approximation for simplicity

PERIOD_THRESHOLD = 5


class PeriodType(IntEnum):
    '''
    Integer Enumeration to specify the types of frequency
    to show the flashcards
    '''
    DAILY, WEEKLY, BIWEEKLY, MONTHLY = range(0, 4)


class FlashCardBot:
    '''
    FlashCard class object
    '''

    def __init__(self,
                 config: dict,
                 database: str = 'flashcard.db',
                 max_attempts: int = 3,
                 timeout: int = 20) -> None:
        '''
        Constructor of FlashCardBot class
        '''

        self.telegrambot = TelegramBot(config['Telegram']['API_KEY'])
        self.pending_item = False
        self.target = []
        self.max_attemps = max_attempts
        self.attempt = 0

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

    def polling(self,
                sleep_time: int = 1):  # pragma: no cover
        '''
        Check incoming message from TelegramBot API
        through  a polling mechanism
        '''

        last_message_id = -1
        while True:
            self.scheduler()
            message_id = self.telegrambot.extract_message_id()

            # Discard first iteration until new incoming message
            if last_message_id == -1:
                last_message_id = message_id

            # Check if new message is available and
            # if incoming message is different from previous one
            if message_id:
                if message_id != last_message_id:
                    msg_type, msg_data = self.telegrambot.check_update()
                    if 'text' == msg_type:
                        message = self.telegrambot.read_message(msg_data)
                        logger.info('Received message = %s', message)
                        self.process_message(message)
                    elif 'photo' == msg_type:
                        self.process_photo(msg_data)
                    last_message_id = message_id

            time.sleep(sleep_time)

    def scheduler(self):
        '''
        Check scheduled flashcards
        '''

        rows = self.cursor.execute('''SELECT * from items''').fetchall()
        for row in rows:
            item_date = datetime.strptime(row[7], DATE_FMT)
            now = datetime.now()
            difference = now - item_date

            # Extract flashcard periodicity type
            period_type = row[4]
            logger.debug('Flashcard type = %s', period_type)

            if not self.pending_item:
                if PeriodType.DAILY == period_type and\
                        difference.total_seconds() >= SECONDS_IN_A_DAY:
                    logger.info('Detected element %s with a diff = %s',
                                row, difference.total_seconds())
                    self.action_show_item(row)
                elif PeriodType.WEEKLY == period_type and\
                        difference.total_seconds() >= SECONDS_IN_A_WEEK:
                    logger.info('Detected element %s with a diff = %s',
                                row, difference.total_seconds())
                    self.action_show_item(row)
                elif PeriodType.BIWEEKLY == period_type and\
                        difference.total_seconds() >= SECONDS_IN_TWO_WEEKS:
                    logger.info('Detected element %s with a diff = %s',
                                row, difference.total_seconds())
                    self.action_show_item(row)
                elif PeriodType.MONTHLY == period_type and\
                        difference.total_seconds() >= SECONDS_IN_A_MONTH:
                    logger.info('Detected element %s with a diff = %s',
                                row, difference.total_seconds())
                    self.action_show_item(row)

    def process_message(self,
                        message: str,
                        delimiter: str = ':'):
        '''
        Extract action from incoming message being
        action defined into <ACTION>: <ITEM> format
        '''

        # Check if there is a pending to answer item,
        # if not, process command
        if self.pending_item:
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

    def process_photo(self,
                      data: dict,
                      item_type: str = 'photo'):
        '''
        Process photo data
        '''

        logger.info('Processing photo')
        file_id = data['photo'][0]['file_id']
        logger.info('File ID = %s', file_id)

        # A picture must be have caption!!
        try:
            caption = data['caption']

            logger.info('Caption = %s', caption)

            now = datetime.strftime(datetime.now(), DATE_FMT)
            self.cursor.execute('''INSERT INTO items (inserted_date, target,
                                    source, period_type,
                                    answer_correct_count, answer_wrong_count,
                                    last_attempt_date, item_type)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                (now, file_id, caption, PeriodType.DAILY,
                                    0, 0, now, item_type))
            self.conn.commit()
            msg = 'Successfully added photo'
            logger.info(msg)
            self.telegrambot.send_message(msg)
        except KeyError:
            msg = 'Please, insert a caption into the photo'
            logger.error(msg)
            self.telegrambot.send_message(msg)

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
                        delimiter: str = '-',
                        item_type: str = 'text'):
        '''
        Save new item into database
        '''

        try:
            now = datetime.strftime(datetime.now(), DATE_FMT)
            word1, word2 = text.split(delimiter)
            word1 = word1.strip()
            word2 = word2.strip()

            self.cursor.execute('''INSERT INTO items (inserted_date, target,
                                source, period_type,
                                answer_correct_count, answer_wrong_count,
                                last_attempt_date, item_type)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                (now, word1, word2, PeriodType.DAILY,
                                 0, 0, now, item_type))
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

    def action_show_item(self,
                         rows=None):
        '''
        Extract randomly item from database
        '''

        if not rows:
            rows = self.cursor.execute('SELECT * from items').fetchall()
            try:
                rows = random.choice(rows)
            except IndexError:
                warning_message = 'No items found in database'
                self.telegrambot.send_message(warning_message)
                logger.warning(warning_message)
        if rows:
            self.target = rows
            if 'text' == self.target[-1]:
                logger.info('Selected row %s', self.target[2])
                logger.info('Send word %s to bot', self.target[2])
                self.telegrambot.send_message(self.target[2])
                now = datetime.strftime(datetime.now(), DATE_FMT)
                self.update_db_field('last_attempt_date', now)
                self.pending_item = True
            elif 'photo' == self.target[-1]:
                file_id = self.target[2]
                self.telegrambot.send_photo(file_id)
                self.pending_item = True

    def process_answer(self,
                       message: str):
        '''
        Check if answer sent via Telegram is correct
        '''
        if message == self.target[3]:
            msg = 'OK!'
            self.telegrambot.send_message(msg)
            logger.info(msg)
            self.process_correct_answer()
            self.reset_answer()
        else:
            self.attempt += 1
            msg = f'ERROR - Current attempt {self.attempt}'
            self.telegrambot.send_message(msg)
            logger.info(msg)
            self.process_wrong_answer()
            if self.attempt >= self.max_attemps:
                self.reset_answer()
                msg = f'Reached max. number of attemps ({self.max_attemps})'
                self.telegrambot.send_message(msg)
                logger.error(msg)

    def process_correct_answer(self):
        '''
        Update correct asnwer count and check type
        '''

        if PeriodType.DAILY == self.target[4] and\
                self.target[5] > PERIOD_THRESHOLD:
            self.update_db_field("period_type", PeriodType.WEEKLY)
            msg = f'Modified {self.target[2]} from Daily to Weekly'
            self.telegrambot.send_message(msg)
            logger.info(msg)
        elif PeriodType.WEEKLY == self.target[4] and\
                self.target[5] > PERIOD_THRESHOLD * 2:
            self.update_db_field("period_type", PeriodType.BIWEEKLY)
            msg = f'Modified {self.target[2]} from Weekly to Bi-Weekly'
            self.telegrambot.send_message(msg)
            logger.info(msg)
        elif PeriodType.BIWEEKLY == self.target[4] and\
                self.target[5] > PERIOD_THRESHOLD * 3:
            self.update_db_field("period_type", PeriodType.MONTHLY)
            msg = f'Modified {self.target[2]} from Bi-Weekly to Monthly'
            self.telegrambot.send_message(msg)
            logger.info(msg)

        self.update_db_numeric_field("answer_correct_count")

    def process_wrong_answer(self):
        '''
        Update wrong answer count and check type
        '''

        self.update_db_numeric_field("answer_wrong_count")
        if self.target[6] > 5:
            if PeriodType.MONTHLY == self.target[4]:
                self.update_db_field("period_type", PeriodType.BIWEEKLY)
                msg = f'Modified {self.target[2]} from Monthly to Bi-Weekly'
                self.telegrambot.send_message(msg)
                logger.info(msg)
            elif PeriodType.BIWEEKLY == self.target[4]:
                self.update_db_field("period_type", PeriodType.WEEKLY)
                msg = f'Modified {self.target[2]} from Bi-Weekly to Weekly'
                self.telegrambot.send_message(msg)
                logger.info(msg)
            elif PeriodType.WEEKLY == self.target[4]:
                self.update_db_field("period_type", PeriodType.DAILY)
                msg = f'Modified {self.target[2]} from Weekly to Daily'
                self.telegrambot.send_message(msg)
                logger.info(msg)

    def reset_answer(self):
        '''
        Reset answer attributes
        '''
        self.target = []
        self.pending_item = False
        self.attempt = 0

    def update_db_field(self,
                        field: str,
                        value):
        '''
        Update a numeric field into database
        '''

        sql_query = f'''UPDATE items
                        SET {field} = '{value}'
                        WHERE target='{self.target[2]}';'''
        self.cursor.execute(sql_query)
        self.conn.commit()
        logger.info('Successfully updated %s', field)

    def update_db_numeric_field(self,
                                field: str):
        '''
        Update a numeric field into database
        '''

        sql_query = f'''UPDATE items
                        SET {field} = {field} + 1
                        WHERE target='{self.target[2]}';'''
        self.cursor.execute(sql_query)
        self.conn.commit()
        logger.info('Successfully updated %s', field)

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

    try:
        with open(configfile, 'rb') as config_reader:
            return tomli.load(config_reader)
    except FileNotFoundError:
        logger.error('Configuration file %s not found', configfile)
        sys.exit(1)


def main():  # pragma: no cover
    '''
    Main function
    '''

    # Check number of arguments
    if len(sys.argv) != 2:
        logger.error("Please execute `python3 flashcard.py <CONFIG>`")
        sys.exit(1)

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
