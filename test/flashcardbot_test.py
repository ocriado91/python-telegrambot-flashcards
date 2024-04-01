import pytest
from flashcard import FlashCardBot, CommandException

@pytest.fixture
def flashcard_bot():
    config = {'Telegram':
              {'API_KEY': 'api_key'},
              'FlashCardBot':
              {'Commands': ['/new_item']}}
    return FlashCardBot(config)


def test_check_command(flashcard_bot):
    '''
    Test TelegramBot check_command method
    '''

    valid_message = {"text": "/new_item"}
    assert "new_item" == flashcard_bot.check_command(valid_message)

    empty_message = {}
    with pytest.raises(CommandException):
        flashcard_bot.check_command(empty_message)

    invalid_type = {"video": "funny cat"}
    with pytest.raises(CommandException):
        flashcard_bot.check_command(invalid_type)

    invalid_command = {"text": "invalid_command"}
    with pytest.raises(CommandException):
        flashcard_bot.check_command(invalid_command)
