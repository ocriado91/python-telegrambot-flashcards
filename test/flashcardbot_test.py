import pytest
import csv
from io import StringIO
from unittest.mock import patch
from flashcard import FlashCardBot, read_config


@pytest.fixture
def flashcard_bot():
    config = {'Telegram':
                {'API_KEY': 'api_key'}}
    return FlashCardBot(config, datafile='test_data.csv', max_attempts=3)


def test_process_action_new(flashcard_bot):
    with patch.object(flashcard_bot, 'action_new_item') as mock_action_new_item:
        flashcard_bot.process_action('new', 'word1 - word2')
        mock_action_new_item.assert_called_once_with('word1 - word2')


def test_process_action_show(flashcard_bot):
    with patch.object(flashcard_bot, 'action_show_item') as mock_action_show_item:
        flashcard_bot.process_action('show', None)
        mock_action_show_item.assert_called_once()


def test_process_action_unknown(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot, 'send_message') as mock_send_message:
        flashcard_bot.process_action('unknown', None)
        mock_send_message.assert_called_once_with('Unknown action unknown')


def test_action_new_item(flashcard_bot):
    with patch('builtins.open', create=True) as mock_open:
        mock_csvfile = mock_open.return_value

        with patch('flashcard.csv.writer') as mock_csvwriter:
            flashcard_bot.action_new_item('word1 - word2')

            # mock_csvwriter.assert_called_once_with(mock_csvfile, delimiter=',')
            mock_csvwriter.return_value.writerow.assert_called_once_with(['word1', 'word2'])
            # assert flashcard_bot.telegrambot.send_message.called


def test_action_new_item_invalid(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot, 'send_message') as mock_send_message:
        flashcard_bot.action_new_item('invalid_item')
        mock_send_message.assert_called_once_with('Invalid item invalid_item')


def test_action_show_item(flashcard_bot):
    with patch('builtins.open', create=True) as mock_open:
        mock_csvfile = mock_open.return_value
        mock_csvfile.__enter__.return_value = StringIO('word1,word2\n')

        with patch.object(flashcard_bot.telegrambot, 'send_message') as mock_send_message:
            flashcard_bot.action_show_item()

            mock_send_message.assert_called_once_with('word1')
            assert flashcard_bot.answer == 'word2'
            assert flashcard_bot.pending_item


def test_action_show_item_no_database(flashcard_bot):
    with patch('builtins.open', side_effect=FileNotFoundError):
        with patch.object(flashcard_bot.telegrambot, 'send_message') as mock_send_message:
            flashcard_bot.action_show_item()
            mock_send_message.assert_called_once_with('No database found')


def test_process_answer_correct(flashcard_bot):
    flashcard_bot.pending_item = True
    flashcard_bot.answer = 'word2'
    with patch.object(flashcard_bot.telegrambot, 'send_message') as mock_send_message:
        flashcard_bot.process_answer('word2')
        mock_send_message.assert_called_once_with('OK!')
        assert not flashcard_bot.pending_item
        assert flashcard_bot.answer is None
        assert flashcard_bot.attempt == 0

def test_process_answer_incorrect(flashcard_bot):
    flashcard_bot.answer = 'word2'

    with patch.object(flashcard_bot.telegrambot, 'send_message') as mock_send_message:
        flashcard_bot.process_answer('wrong_answer')

        mock_send_message.assert_called_once_with('ERROR - Current attempt 1')
        assert flashcard_bot.attempt == 1
        assert not flashcard_bot.pending_item


def test_process_answer_max_attempts(flashcard_bot):
    flashcard_bot.answer = 'word2'
    flashcard_bot.attempt = 2

    with patch.object(flashcard_bot.telegrambot, 'send_message') as mock_send_message:
        flashcard_bot.process_answer('wrong_answer')
        assert flashcard_bot.attempt == 0
        assert not flashcard_bot.pending_item

def test_process_message(flashcard_bot):
    # Test when there is no pending item
    flashcard_bot.pending_item = False

    # Case 1: Message without delimiter
    message = 'show'
    with patch.object(flashcard_bot, 'process_action') as mock_process_action:
        flashcard_bot.process_message(message)
        assert mock_process_action.call_count == 1  # process_action should not be called
        flashcard_bot.process_action.assert_called_once_with('show', None)  # process_action should be called with the correct parameters

    # Case 2: Message with delimiter
    message = 'new:item'
    with patch.object(flashcard_bot, 'process_action') as mock_process_action:
        flashcard_bot.process_message(message)
        assert mock_process_action.call_count == 1  # process_action should not be called
        flashcard_bot.process_action.assert_called_once_with('new', 'item')  # process_action should be called with the correct parameters

    # Test when there is a pending item
    flashcard_bot.pending_item = True

    # Case 3: Message with pending item
    message = 'answer'
    with patch.object(flashcard_bot, 'process_answer') as mock_process_answer:
        with patch.object(flashcard_bot, 'process_action') as mock_process_action:
            flashcard_bot.process_message(message)
            mock_process_answer.assert_called_once_with('answer')  # process_answer should be called with the correct parameter
            assert mock_process_action.call_count == 0  # process_action should not be called

def test_read_config():
    config = read_config('config/template.toml')
    assert config['Telegram']['API_KEY'] == "<YOUR_API_KEY>"

