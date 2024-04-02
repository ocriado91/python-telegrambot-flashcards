#!/usr/bin/env python3
'''
Configuration Handler
'''

import logging
from typing import List

import pydantic
from pydantic import BaseModel

import tomli

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TelegramBotConfig(BaseModel):
    ''' TelegramBot Configuration Model'''
    API_KEY: str

class FlashCardBotConfig(BaseModel):
    ''' FlashCard Bot Configuration Model'''
    Commands: List[str]
    SleepTime: int

class TOMLConfig(BaseModel):
    ''' Configuration model '''
    Telegram: TelegramBotConfig
    FlashCardBot: FlashCardBotConfig


class ConfigurationException(Exception):
    '''
    Custom Configuration exception
    '''
    def __init__(self,
                 message):
        super().__init__(message)


class Configuration:
    '''
    Class to manage TOML configuration file
    '''
    def __init__(self,
                 configuration_file: str):

        self.configuration_file = configuration_file

    def validate(self) -> dict:
        '''
        Validate TOML configuration file using pydantic models

        Returns:
            - dict: TOML configuration file data
        '''

        # Read configuration file data and try to validate it
        # against pydantic model
        data = self.read()
        try:
            TOMLConfig(**data)
        except pydantic.ValidationError as exception:
            raise ConfigurationException(
                f"Configuration file validation error: {exception}") \
                    from exception
        return data


    def read(self):
        '''
        Read TOML configuration file
        '''
        try:
            with open(self.configuration_file, 'rb') as config_reader:
                return tomli.load(config_reader)
        except FileNotFoundError as exception:
            raise ConfigurationException(
                f'{self.configuration_file} not found') from exception
