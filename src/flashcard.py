#!/usr/bin/env python3
'''
A TelegramBot to learn new words
'''

from datetime import datetime, timezone

import logging
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

    def new_item(self, message):
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

    def polling(self) -> None:  # pragma: no cover
        '''
        Check incoming message from TelegramBot API
        through  a polling mechanism
        '''

        # Define a {command: function} to execute a determine
        # function based on incoming command
        switcher = {
            "new_item": self.new_item,
            "new_round": self.new_round
        }

        # Initialize variables
        pending_command = False
        command = ''
        attempt_count = 0
        max_attemps = self.config['FlashCardBot']['MaxAttempts']

        reference_time = datetime.now(timezone.utc)
        # Start polling mechanism
        while True:
            try:
                # Check if there is a new message
                if self.telegrambot.check_new_message(reference_time):
                    # Extract raw incoming message
                    message = self.telegrambot.check_message_type()

                    # None pending command, waiting to receive a new one
                    if not pending_command:
                        command = self.check_command(message)
                        logger.info("Detected command %s", command)

                        if command == "new_item":
                            msg = "Please, add the new item 😊"
                            self.telegrambot.send_message(msg)
                            pending_command = True
                        elif command == "new_round":
                            item = self.storage_manager.select_random_item()
                            if not item:
                                msg = "None item detected in database"
                                logger.error(msg)
                                self.telegrambot.send_message(msg)
                            else:
                                quiz = item[3]
                                logger.info("Sending %s as quiz", quiz)
                                self.telegrambot.send_message(quiz)
                                pending_command = True
                        else:
                            msg = "Command not found"
                            logger.error(msg)
                            self.telegrambot.send_message(msg)
                    else:
                        logger.info("Trying to process %s with command %s",
                                    message,
                                    command)
                        # Select the command function in based on
                        # pending command
                        command_function = switcher.get(command)
                        result = command_function(message)
                        if not result:
                            if attempt_count == max_attemps:
                                msg = "Reached max. attempts."
                                logger.error(msg)
                                self.telegrambot.send_message(msg)
                                # Reset pending command flag and attempt counter
                                pending_command = False
                                attempt_count = 0
                                continue
                            attempt_count += 1
                            logger.warn("Number of attempts: %s", attempt_count)
                            continue

                        # Incoming message processed. Time to flush pending
                        # command flag
                        logger.info("💪 Successfully processed command")
                        pending_command = False
                        attempt_count = 0

                time.sleep(self.config['FlashCardBot']['SleepTime'])

            except CommandException as error:
                logger.error("Command error: %s", error)
                self.telegrambot.send_message("error")
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
