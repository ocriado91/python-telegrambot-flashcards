#!/usr/bin/env python3
'''
A TelegramBot to learn new words
'''

import csv
import logging
import random
import sys
import time
import tomli

from telegrambot import TelegramBot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)


class FlashCardBot:
    '''
    FlashCard class object
    '''

    def __init__(self,
                 config: dict,
                 datafile: str = 'data.csv',
                 max_attempts: int = 3) -> None:
        '''
        Constructor of FlashCardBot class
        '''

        self.config = config
        self.datafile = datafile
        self.telegrambot = TelegramBot(config['Telegram']['API_KEY'])
        self.pending_item = False
        self.answer = None
        self.max_attemps = max_attempts
        self.attempt = 0

    def polling(self,
                sleep_time: int = 1):
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
            logger.info('Applying New Item action')
            self.action_new_item(item)
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
            word1, word2 = text.split(delimiter)
            word1 = word1.strip()
            word2 = word2.strip()
            with open(self.datafile, 'a',
                      newline='', encoding='UTF-8') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow([word1, word2])
            msg = f'Successfully added new item {word1} - {word2}'
            self.telegrambot.send_message(msg)
            logging.info(msg)
        except ValueError:
            warning_message = f'Invalid item {text}'
            self.telegrambot.send_message(warning_message)
            logger.warning(warning_message)

    def action_show_item(self):
        '''
        Extract randomly item from datafile
        '''

        try:
            with open(self.datafile, 'r', encoding='UTF-8') as csvfile:
                csvreader = csv.reader(csvfile)
                rows = list(csvreader)
                selected_row = random.choice(rows)
                logger.info('Selected row %s', selected_row)
                word1 = selected_row[0]
                self.answer = selected_row[1]
                logger.info('Send word %s to bot', word1)
                self.telegrambot.send_message(word1)
                self.pending_item = True

        except FileNotFoundError:
            msg = 'No database found'
            self.telegrambot.send_message(msg)
            logger.info(msg)

    def process_answer(self,
                       message: str):
        '''
        Check if answer sent via Telegram is correct
        '''
        if message == self.answer:
            msg = 'OK!'
            self.telegrambot.send_message(msg)
            logger.info(msg)
            self.reset_answer()
        else:
            self.attempt += 1
            msg = f'ERROR - Current attempt {self.attempt}'
            self.telegrambot.send_message(msg)
            logger.info(msg)
            if self.attempt >= self.max_attemps:
                self.reset_answer()
                msg = f'Reached max. number of attemps ({self.max_attemps})'
                self.telegrambot.send_message(msg)
                logger.error(msg)

    def reset_answer(self):
        '''
        Reset answer attributes
        '''
        self.answer = None
        self.pending_item = False
        self.attempt = 0


def read_config(configfile: str) -> dict:
    '''
    Read TOM configuration file and extract fields
    '''

    with open(configfile, 'rb') as config_reader:
        config = tomli.load(config_reader)

    return config


def main():
    '''
    Main function
    '''

    # Read configuration file
    config = read_config(sys.argv[1])

    # Built FlashCard Bot object
    bot = FlashCardBot(config)

    # Start polling mechanism
    bot.polling()


if __name__ == '__main__':
    main()
