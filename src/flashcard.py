#!/usr/bin/env python3
'''
A TelegramBot to learn new words
'''

import logging
import sys
import time

from telegrambot import TelegramBot

from configuration import Configuration
from storage_manager import StorageManager, StorageManagerException

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CommandException(Exception):
    '''
    Raised when try to use a non-text value as command
    '''
    def __init__(self,
                 message):
        super().__init__(message)

class FlashCardBot:
    '''
    FlashCard class object
    '''

    def __init__(self,
                 config: dict) -> None:
        '''
        Constructor of FlashCardBot class
        '''

        # Store configuration data as attribute
        self.config = config

        # Init Telegram Bot
        self.telegrambot = TelegramBot(self.config['Telegram'])

        # Init StorageManager
        self.storage_manager = StorageManager()

    def check_command(self,
                      message: str) -> str:
        '''
        Check if message is a valid command

        Parameters:
            - message (dictionary): Incoming message to check as valid command

        Returns:
            - str: Detected command name into message
        '''
        logger.info("Checking message %s into %s commands",
                     message,
                     self.config['FlashCardBot']['Commands'])

        # In case of unsupported format, the TelegramBot package
        # returns a None object. To check this case
        if not message:
            raise CommandException("Incoming message is empty")

        # Check if message type is text
        if "text" not in message.keys():
            raise CommandException("Non-text tried to use as command")

        # Check if message text contains a valid command
        command = list(message.values())[0]
        if command not in self.config['FlashCardBot']['Commands']:
            raise CommandException(f"Invalid command {command}")

        return command.replace('/', '')

    def new_item(self, message):
        '''
        Method to add a new element based on message
        '''
        logger.info("Adding new item %s", message)
        item_type = list(message.keys())[0]
        if item_type == "text":
            text = message[item_type]
            target, source = text.split('-')
            self.storage_manager.insert_item(item_type,
                                             target,
                                             source)
            msg = f'Successfully added new item {target} - {source}'
            self.telegrambot.send_message(msg)
            logging.info(msg)
        elif item_type == "photo":
            photo_info = message[item_type]
            logger.info("Photo info: %s", photo_info)
        elif item_type == "video":
            video_info = message[item_type]
            logger.info("Video info: %s", video_info)
        elif item_type == "audio":
            audio_info = message[item_type]
            logger.info("Audio info: %s", audio_info)

    def process_text(self,
                     text: str) -> None:
        '''
        Process text item
        '''


    def new_round(self):
        '''
        Method to start a new round
        '''
        logging.info("Starting new round!!")

    def show_stats(self):
        '''
        Method to show statistics
        '''
        logger.info("Showing statistics!!")



    def polling(self):  # pragma: no cover
        '''
        Check incoming message from TelegramBot API
        through  a polling mechanism
        '''
        switcher = {
            "new_item": self.new_item,
            "new_round": self.new_round,
            "show_stats": self.show_stats
        }
        pending_command = False
        command = ''
        while True:
            try:
                if self.telegrambot.check_new_message():
                    # Extract raw incoming message
                    message = self.telegrambot.check_message_type()

                    # None pending command, waiting to receive a new one
                    if not pending_command:
                        command = self.check_command(message)
                        logger.info("Detected command %s", command)
                        pending_command = True
                    else:
                        logger.info("Trying to process %s with command %s",
                                    message,
                                    command)
                        command_function = switcher.get(command)
                        command_function(message)

                        # Incoming message processed. Time to flush pending
                        # command flag
                        logger.info("Successfully processed command")
                        pending_command = False

                time.sleep(self.config['FlashCardBot']['SleepTime'])

            except CommandException as error:
                logger.error("Command error: %s", error)
                continue

            except StorageManagerException as error:
                logger.error("Storage Manager error: %s", error)
                self.telegrambot.send_message(error)
                continue

            except KeyboardInterrupt:
                logger.error("Detected Keyboard Interrupt. Bye!")
                self.storage_manager.close_connection()
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
    config = Configuration(sys.argv[1]).read()

    # Built FlashCard Bot object
    bot = FlashCardBot(config)

    # Start polling mechanism
    bot.polling()


if __name__ == '__main__':  # pragma: no cover
    main()
