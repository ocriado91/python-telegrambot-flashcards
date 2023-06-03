#!/usr/bin/env python3

''' Telegram Bot API based on official Telegram Bot API requests
    Reference: https://core.telegram.org/bots/api s'''


import logging
import requests

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

    def read_message(self,
                     data: dict):
        '''
        Read message from official TelegramBot API request
        '''
        return data['text']

    def send_message(self,
                     message: str):
        '''
        Send message from official TelegramBot API request
        '''
        self.get_chat_id()
        # Build API request
        url = f'''https://api.telegram.org/bot{self.api_key}/sendMessage'''
        logger.info('Sending message %s to %s', message, self.chat_id)

        # Post request
        requests.post(url,
                      timeout=10,
                      data={'chat_id': self.chat_id,
                            'text': message}).json()

    def send_photo(self,
                   file_id: str):
        '''
        Send photo from official TelegramBot API
        '''

        self.get_chat_id()

        # Build API request
        url = f'''https://api.telegram.org/bot{self.api_key}/sendPhoto'''
        requests.post(url,
                      timeout=10,
                      data={'chat_id': self.chat_id,
                            'photo': file_id}).json()

    def check_update(self):
        '''
        Check incoming update from Telegram Bot
        '''

        url = f'''https://api.telegram.org/bot{self.api_key}/getUpdates'''
        logger.info('Extract data from %s', url)
        data = requests.post(url,
                             timeout=10,
                             data={'offset': -1}).json()

        update_data = data['result'][0]['message']
        logger.info(update_data)

        if 'text' in update_data.keys():
            return 'text', update_data

        if 'photo' in update_data.keys():
            return 'photo', update_data

        return None, None
