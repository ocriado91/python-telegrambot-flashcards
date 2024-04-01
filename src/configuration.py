#!/usr/bin/env python3
'''
Configuration Handler
'''

import logging
import sys

import tomli

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Configuration:
    '''
    Class to manage TOML configuration file
    '''
    def __init__(self,
                 configuration_file: str):
        self.configuration_file = configuration_file

    def read(self) -> dict:
        '''
        Read TOML configuration file
        '''
        try:
            with open(self.configuration_file, 'rb') as config_reader:
                return tomli.load(config_reader)
        except FileNotFoundError:
            logger.error('Configuration file %s not found',
                         self.configuration_file)
            sys.exit(1)
