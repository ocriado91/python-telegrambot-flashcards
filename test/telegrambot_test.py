import pytest
import os
from unittest.mock import patch
from telegrambot import TelegramBot

@pytest.fixture
def telegram_bot():
    api_key = os.environ.get('TELEGRAM_API_KEY')
    return TelegramBot(api_key=api_key)

@patch('telegrambot.requests.post')
def test_get_chat_id(mock_post, telegram_bot):
    # Mock the response from the API
    mock_post.return_value.json.return_value = {
        'result': [
            {
                'message': {
                    'chat': {'id': 123}
                }
            }
        ]
    }

    telegram_bot.get_chat_id()

    assert telegram_bot.chat_id == 123

@patch('telegrambot.requests.post')
def test_get_none_chat_id(mock_post, telegram_bot):
    # Mock the response from the API
    mock_post.return_value.json.return_value = {
        'result': []
    }

    telegram_bot.get_chat_id()

    assert telegram_bot.chat_id == None

@patch('telegrambot.requests.post')
def test_extract_message_id(mock_post, telegram_bot):
    # Mock the response from the API
    mock_post.return_value.json.return_value = {
        'result': [
            {'update_id': 1},
            {'update_id': 2},
            {'update_id': 3}
        ]
    }

    message_id = telegram_bot.extract_message_id()

    assert message_id == 3

@patch('telegrambot.requests.post')
def test_extract_none_message_id(mock_post, telegram_bot):
    # Mock the response from the API
    mock_post.return_value.json.return_value = {
        'result': []
    }

    message_id = telegram_bot.extract_message_id()

    assert message_id == None

@patch('telegrambot.requests.post')
def test_read_message(mock_post, telegram_bot):
    # Mock the response from the API
    mock_post.return_value.json.return_value = {
        'result': [
            {
                'message': {'text': 'Hello World',
                            'chat': {'id': 123}}
            }
        ]
    }

    message = telegram_bot.read_message()

    assert message == 'Hello World'

@patch('telegrambot.requests.post')
def test_send_message(mock_post, telegram_bot):
    # Mock the response from the API
    mock_post.return_value.json.return_value = {
        'ok': True
    }

    telegram_bot.chat_id = 123
    telegram_bot.send_message('Test message')

    # Extract API key for environment variable
    api_key = os.environ.get('TELEGRAM_API_KEY')

    # Check if the API request was made with the correct parameters
    mock_post.assert_called_with(
        f'https://api.telegram.org/bot{api_key}/sendMessage',
        timeout=10,
        data={'chat_id': 123, 'text': 'Test message'}
    )
