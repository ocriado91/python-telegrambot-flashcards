#!/usr/bin/env python3

''' Telegram Bot API based on official Telegram Bot API requests
    Reference: https://core.telegram.org/bots/api s'''


import logging
import sys
import requests
import tomli

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot():
    '''
    Telegram Bot Class
    '''

    def __init__(self,
                 api_key: str):
        self.api_key = api_key
        self.chat_id = None
        logger.info("Initialised Telegrambot")

    def get_chat_id(self):
        '''
        Extract chat ID TelegramBot field
        '''
        url = f'''https://api.telegram.org/bot{self.api_key}/getUpdates'''
        data = requests.post(url,
                             timeout=10,
                             data={'offset': -1}).json()
        if data['result']:
            self.chat_id = data['result'][0]['message']['chat']['id']
        else:
            self.chat_id = None

    def extract_message_id(self):
        '''
        Extract the message identifier
        '''

        url = f'''https://api.telegram.org/bot{self.api_key}/getUpdates'''
        data = requests.post(url,
                             timeout=10,
                             data={'offset': -1}).json()

        # Extract the chat ID field from the newest incoming message
        if data['result']:
            return data['result'][-1]['update_id']
        logger.warning('No detected messages.\
            Plese send a message to bot to establish communication')
        return None

    def read_message(self):
        '''
        Read message from official TelegramBot API request
        '''

        url = f'''https://api.telegram.org/bot{self.api_key}/getUpdates'''
        logger.info('Extract data from %s', url)
        data = requests.post(url,
                             timeout=10,
                             data={'offset': -1}).json()

        self.get_chat_id()
        return data['result'][0]['message']['text']

    def send_message(self,
                     message: str):
        '''
        Sent message from official TelegramBot API request
        '''

        # Build API request
        url = f'''https://api.telegram.org/bot{self.api_key}/sendMessage'''
        logger.info('Sending message %s to %s', message, self.chat_id)

        # Post request
        requests.post(url,
                      timeout=10,
                      data={'chat_id': self.chat_id,
                            'text': message}).json()


def read_config(configfile: str) -> str:
    '''
    Read TOML configfile and extract
    Telegram API key field
    '''

    with open(configfile, 'rb') as config_reader:
        config = tomli.load(config_reader)

    return config['Telegram']['API_KEY']


def main():
    '''
    Main function
    Echo of the latest message sent to Telegram Bot
    '''

    # Read configfile
    config = sys.argv[1]
    api_key = read_config(config)

    # Create Telegram object
    telegrambot = TelegramBot(api_key)

    message = telegrambot.read_message()
    telegrambot.send_message(message)


if __name__ == '__main__':
    main()
