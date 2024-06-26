import os
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
                    'Commands': ['/new_item', '/new_round'],
                    'SleepTime': 1,
                    'Database': 'test_database.db',
                    'Timeout': 20,
                    'MaxAttempts': 3,
                    'DownloadPath': 'download/'
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

def test_processing_command_new_item(flashcard_bot):
    '''
    Test new_item command processing functionality
    '''

    message = {"text": "/new_item"}
    command = flashcard_bot.processing_command(message)
    assert command == "new_item"

def test_processing_command_new_round(flashcard_bot):
    '''
    Test new_round command processing functionality
    '''

    # Insert a dummy item to database
    message = {"text": "Hello - Hola"}
    flashcard_bot.new_item(message)

    # Check new_round command processing
    command_message = {"text": "/new_round"}
    command = flashcard_bot.processing_command(command_message)
    assert command == "new_round"

def test_new_item_document(flashcard_bot):
    '''
    Test adding new item import CSV file. The method returns False due to
    none existing file into download folder.
    '''

    command_message = {"document": "1234ABCD"}
    assert not flashcard_bot.new_item(command_message)

def test_import_csv_file(flashcard_bot):
    '''
    Test import CSV file functionality
    '''

    # Create a CSV file into download folder and write a single row
    with open("download/test_data.csv", "w", encoding="utf-8") as file_obj:
        file_obj.write("Cat,Gato")

    with patch("telegrambot.TelegramBot.download_file") as mock_download:
        assert flashcard_bot.import_csv_file(file_id="1234ABCD")
        mock_download.assert_called_once()

def test_import_csv_file_empty_files(flashcard_bot):
    '''
    Test import a non-existing CSV file
    '''

    with patch("telegrambot.TelegramBot.download_file") as mock_download:
        assert not flashcard_bot.import_csv_file(file_id="1234ABCD")
        mock_download.assert_called_once()

def test_import_csv_file_item_already_stored(flashcard_bot):
    '''
    Test import CSV file functionality trying to import the same item twice
    '''

    # Create a CSV file into download folder and write a single row
    with open("download/test_data.csv", "w", encoding="utf-8") as file_obj:
        file_obj.write("Cat,Gato\n")
        file_obj.write("Cat,Gato")

    with patch("telegrambot.TelegramBot.download_file") as mock_download:
        assert flashcard_bot.import_csv_file(file_id="1234ABCD")
        mock_download.assert_called_once()

# Remove test database after execution
@pytest.fixture(scope='session', autouse=True)
def setup_tests():
    '''
    Create a download folder before test execution and remove the database
    when the test ends.
    '''
    os.mkdir("download/")
    yield
    os.remove("test_database.db")
