#!/usr/bin/env python3

from telegrambot import TelegramBot
import sys
import logging
import time
import tomli

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)


def polling(telegrambot: TelegramBot):
    '''
    Check incoming message from TelegramBot API
    through  a polling mechanism
    '''

    last_message_id = -1
    while True:
        message_id = telegrambot.extract_message_id()

        # Discard first iteration until new incoming message
        if last_message_id == -1:
            last_message_id = message_id

        # Check if new message is available and
        # if incoming message is different from previous one
        if message_id:
            if message_id != last_message_id:
                message = telegrambot.read_message()
                logger.info(f'Received message = {message}')
                telegrambot.send_message(message)
                last_message_id = message_id

        time.sleep(1)

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

    # Build Telegram bot object
    telegrambot = TelegramBot(config['Telegram']['API_KEY'])

    # Launch polling mechanism
    polling(telegrambot)

if __name__ == '__main__':
    main()