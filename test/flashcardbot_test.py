import pytest
from flashcard import FlashCardBot, CommandException

from unittest.mock import patch

@pytest.fixture
def flashcard_bot():
    config = {'Telegram':
                {
                    'API_KEY': 'api_key'
                },
              'FlashCardBot':
              {
                    'Commands': ['/new_item'],
                    'SleepTime': 1,
                    'Database': 'test_database.db',
                    'Timeout': 20
              }
            }
    return FlashCardBot(config)


def test_check_command(flashcard_bot):
    '''
    Test TelegramBot check_command method
    '''
    valid_message = {"text": "/new_item"}
    assert "new_item" == flashcard_bot.check_command(valid_message)

def test_check_command_empty_message(flashcard_bot):
    '''
    The TelegramBot API package, returns a None in case of non-supported format
    message
    '''

    empty_message = {}
    with pytest.raises(CommandException):
        flashcard_bot.check_command(empty_message)

def test_check_invalid_type(flashcard_bot):
    '''
    Test case of invalid type as command
    '''

    invalid_type = {"video": "funny cat"}
    with pytest.raises(CommandException):
        flashcard_bot.check_command(invalid_type)

def test_check_invalid_command(flashcard_bot):
    '''
    Test to check a non-supported command incoming
    '''

    invalid_command = {"text": "invalid_command"}
    with pytest.raises(CommandException):
        flashcard_bot.check_command(invalid_command)

def test_new_round(flashcard_bot):
    '''
    Test new round method
    '''

    message = {"text": "testA"}
    with patch("flashcard.StorageManager.check_quiz_item") as mock_storage:
        mock_storage.return_value = True
        assert flashcard_bot.new_round(message)

def test_new_round_wrong(flashcard_bot):
    '''
    Test new round method
    '''

    message = {"text": "testA"}
    with patch("flashcard.StorageManager.check_quiz_item") as mock_storage:
        mock_storage.return_value = False
        assert not flashcard_bot.new_round(message)

def test_new_text_item(flashcard_bot):
    '''
    Test to check adding process a new text item
    '''
    message = {"text": "Hello - Hola"}

    with patch("flashcard.StorageManager.insert_item") as mock_new_item:
        flashcard_bot.new_item(message)
        mock_new_item.assert_called_once_with("text",
                                              "Hello",
                                              "Hola")

def test_new_photo_item(flashcard_bot):
    '''
    Test to check adding process a new text item
    '''
    message = {"photo": ("Cat", "2wrgvweghrv4")}

    with patch("flashcard.StorageManager.insert_item") as mock_new_item:
        flashcard_bot.new_item(message)
        mock_new_item.assert_called_once_with("photo",
                                              "2wrgvweghrv4",
                                              "Cat")

