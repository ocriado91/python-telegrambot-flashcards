#!/usr/bin/env python3

''' Telegram Bot API based on official Telegram Bot API requests
    Reference: https://core.telegram.org/bots/api s'''


import logging
import sys
import requests
import tomli

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TelegramBot():
    ''' Telegram Bot Class '''

    def __init__(self,
                 api_key: str):
        self.api_key = api_key
        self.chat_id = None
        logger.info("Initialised Telegrambot")

    def get_chat_id(self):
        """ Extract chat ID TelegramBot field """
        url = f'''https://api.telegram.org/bot{self.api_key}/getUpdates'''
        data = requests.post(url, timeout=10).json()
        logger.debug(data['result'][-1])
        if data['result']:
            self.chat_id = data['result'][-1]['message']['chat']['id']
        else:
            self.chat_id = None

    def read_message(self):
        ''' Read message from official TelegramBot API request '''

        url = f'''https://api.telegram.org/bot{self.api_key}/getUpdates'''
        logger.debug('Extract data from %s', url)
        data = requests.post(url, timeout=10).json()

        # Extract text from last incoming data
        message = data['result'][-1]['message']['text']
        self.chat_id = data['result'][-1]['message']['chat']['id']
        return message

    def send_message(self,
                     message: str):
        ''' Sent message from official TelegramBot API request '''

        # Update chat ID attribute
        # self.get_chat_id()

        # Build API request
        url = f'''https://api.telegram.org/bot{self.api_key}/sendMessage'''
        data = {'chat_id': self.chat_id, 'text': message}
        logger.info('Sending message %s to %s', message, self.chat_id)

        # Post request
        requests.post(url, data, timeout=10).json()

def read_config(configfile: str) -> str:
    '''
    Read TOML configfile and extract
    Telegram API key field
    '''

    with open(configfile, 'rb') as config_reader:
        config = tomli.load(config_reader)

    return config['Telegram']['API_KEY']

def main():
    ''' Main function '''

    # Read configfile
    config = sys.argv[1]
    api_key = read_config(config)

    # Echo received text
    telegrambot = TelegramBot(api_key)
    # message = telegrambot.read_message()
    telegrambot.send_message("Helloooo")

if __name__ == '__main__':
    main()
