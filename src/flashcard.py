#!/usr/bin/env python3
'''
A TelegramBot to learn new words
'''

from datetime import datetime, timezone

import logging
import os
import sys
import time

from telegrambot import TelegramBot

from configuration import Configuration, ConfigurationException
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
        self.storage_manager = StorageManager(
            database=self.config['FlashCardBot']['Database'],
            timeout=self.config['FlashCardBot']['Timeout'])

    def check_command(self,
                      message: dict) -> str:
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

    def import_csv_file(self,
                        file_id: str) -> bool:
        '''
        Import a CSV file and insert its contents
        into the database

        Parameters:
            -  file_id (str): Telegram Bot API File ID of the file to be
                downloaded

        Returns:
            - bool: Flag to report method status
        '''

        download_path = self.config["FlashCardBot"]["DownloadPath"]

        # Try to download incoming file
        self.telegrambot.download_file(
            file_id,
            download_path
        )

        download_files = os.listdir(download_path)
        if not download_files:
            logger.warning("None detected file into %s", download_path)
            return False

        # Concatenate path and read downloaded file
        download_file = os.path.join(download_path, download_files[0])
        logger.info(download_file)
        with open(download_file, encoding='utf-8') as file_obj:
            lines = file_obj.readlines()

        # Remove break line characters
        lines = [line.replace('\n', '') for line in lines]

        # Insert all items into database
        for line in lines:
            answer, quiz = line.split(',')
            try:
                self.storage_manager.insert_item("text",
                                                answer,
                                                quiz)
            except StorageManagerException:
                logger.warning("Item %s already stored", answer)
                continue

        # Remove downloaded file
        os.remove(download_file)

        return True

    def new_item(self, message) -> bool:
        '''
        Method to add a new element based on message

        Parameters:
            - message (dictionary): Incoming message with item data
        '''
        logger.info("Adding new item %s", message)

        # Extract item type from message
        item_type = list(message.keys())[0]

        answer = ''
        quiz = ''
        if item_type == "text":
            # Extract the answer and quiz fields from text.
            # NOTE: the text value have "answer - quiz" format.
            text = message[item_type]
            answer, quiz = text.split('-')

            # Remove leading and trailing whitespaces
            answer = answer.strip()
            quiz = quiz.strip()
        elif item_type == "document":
            file_id = message[item_type]
            if not self.import_csv_file(file_id):
                return False
        else:
            # Use the file_id field as quiz and caption as answer
            quiz, answer = message[item_type]

        # Insert into StorageManager
        self.storage_manager.insert_item(item_type,
                                         answer,
                                         quiz)

        # Report to user
        msg = f"Successfully added new answer {answer}"
        self.telegrambot.send_message(msg)
        logging.info(msg)
        return True

    def new_round(self, message):
        '''
        Method to start a new round
        '''
        attempt = message["text"]
        match = self.storage_manager.check_quiz_item(attempt)
        logger.info("Matched? %s", match)
        if match:
            self.telegrambot.send_message("Correct!🎉")
        else:
            self.telegrambot.send_message("Wrong answer 🥲")
        return match

    def processing_command(self, message: str) -> str:
        '''
        Processing command in based on message

        Parameters:
            - message (str): Incoming message to decode command

        Returns:
            str: Detected command
        '''

        send_quiz_switcher = {
            "text": self.telegrambot.send_message,
            "photo": self.telegrambot.send_photo,
            "audio": self.telegrambot.send_audio,
            "video": self.telegrambot.send_video
        }
        command = self.check_command(message)

        if command == "new_item":
            msg = "Please, add the new item 😊"
            self.telegrambot.send_message(msg)
        elif command == "new_round":
            quiz, item_type = \
                self.storage_manager.select_random_item()

            # Select the properly function to send the quiz
            # to the user depending on item type
            send_quiz_switcher.get(item_type)(quiz)

        return command

    def polling(self) -> None:  # pragma: no cover
        '''
        Check incoming message from TelegramBot API
        through  a polling mechanism
        '''

        # Define a {command: function} dictionary to execute a determine
        # function based on incoming command
        switcher = {
            "new_item": self.new_item,
            "new_round": self.new_round
        }

        # Initialize variables
        command = ''
        attempt_count = 0
        reference_time = datetime.now(timezone.utc)
        max_attempts = self.config['FlashCardBot']['MaxAttempts']

        # Start polling mechanism
        while True:
            try:
                # Check if there is a new message
                if self.telegrambot.check_new_message(reference_time):
                    # Extract raw incoming message
                    message = self.telegrambot.check_message_type()

                    # None pending command, waiting to receive a new one
                    if not command:
                        command = self.processing_command(message)
                        continue

                    # Select the command function in based on pending command
                    result = switcher.get(command)(message)
                    if not result:
                        if attempt_count == max_attempts:
                            msg = "Reached max. attempts."
                            logger.error(msg)
                            self.telegrambot.send_message(msg)
                            # Reset command and attempt_count values
                            command = ''
                            attempt_count = 0
                            continue

                        attempt_count += 1
                        logger.warning("Number of attempts: %s",
                                        attempt_count)
                        continue

                    # Incoming message processed
                    command = ''
                    attempt_count = 0

                time.sleep(self.config['FlashCardBot']['SleepTime'])

            except CommandException as error:
                logger.error("Command error: %s", error)
                self.telegrambot.send_message(error)
                continue

            except StorageManagerException as error:
                logger.error("Storage Manager error: %s", error)
                self.telegrambot.send_message(error)
                continue

            except ValueError as error:
                logger.error("ValueError: %s", error)
                msg = "🧐 Something went wrong. Please try again"
                self.telegrambot.send_message(msg)
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

    # Validate configuration file and extract configuration data
    try:
        config = Configuration(sys.argv[1]).validate()
    except ConfigurationException as exception:
        logger.error("Configuration error: %s", exception)
        sys.exit(1)

    # Built FlashCard Bot object
    bot = FlashCardBot(config)

    # Start polling mechanism
    bot.polling()


if __name__ == '__main__':  # pragma: no cover
    main()
