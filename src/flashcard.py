#!/usr/bin/env python3
'''
A TelegramBot to learn new words
'''

import csv
import logging
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
                 datafile: str = 'data.csv') -> None:
        '''
        Constructor of FlashCardBot class
        '''

        self.config = config
        self.datafile = datafile
        self.telegrambot = TelegramBot(config['Telegram']['API_KEY'])

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

        try:
            action, item = message.split(delimiter)

            # Convert action to lowercase
            action = action.lower()

            # Trim whitespaces
            action = action.strip()
            item = item.strip()

            logger.info('Detected action %s with text %s', action, item)
            self.process_action(action, item)
        except ValueError:
            warning_message = f'No detected action for message: {message}'
            self.telegrambot.send_message(warning_message)
            logger.warning(warning_message)

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
        elif action == 'remove':
            logger.info('Removing item')
        elif action == 'show':
            logger.info('Showing item')
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
