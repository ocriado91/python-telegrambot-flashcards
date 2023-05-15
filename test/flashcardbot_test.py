import pytest
from unittest.mock import patch
from flashcard import FlashCardBot, read_config


@pytest.fixture
def flashcard_bot():
    config = {'Telegram':
              {'API_KEY': 'api_key'}}
    return FlashCardBot(config, database='test_data.db', max_attempts=3)


def test_process_action_new(flashcard_bot):
    with patch.object(flashcard_bot,
                      'action_new_item') as mock_action_new_item:
        flashcard_bot.process_action('new', 'word1 - word2')
        mock_action_new_item.assert_called_once_with('word1 - word2')


def test_process_action_show(flashcard_bot):
    with patch.object(flashcard_bot,
                      'action_show_item') as mock_action_show_item:
        flashcard_bot.process_action('show', None)
        mock_action_show_item.assert_called_once()


def test_process_action_unknown(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.process_action('unknown', None)
        mock_send_message.assert_called_with('Unknown action unknown')


def test_action_new_item(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:

        # Test adding a new item
        flashcard_bot.action_new_item('word1 - word2')
        # Verify that the item is added to the database
        flashcard_bot.cursor.execute('SELECT * FROM items WHERE target=?',
                                     ('word1',))
        result = flashcard_bot.cursor.fetchone()
        assert result is not None
        assert result[1] == 'word1'
        assert result[2] == 'word2'
        msg = 'Successfully added new item word1 - word2'
        mock_send_message.assert_called_once_with(msg)

    # Test adding a duplicate item
    flashcard_bot.action_new_item('word1 - word2')

    # Verify that the duplicate item is not added
    flashcard_bot.cursor.execute('''SELECT COUNT(*)
                                 FROM items WHERE target=?''', ('word1',))
    result = flashcard_bot.cursor.fetchone()
    assert result[0] == 1  # Should still have only 1 item with target 'apple'


def test_action_new_item_invalid(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.action_new_item('invalid_item')
        mock_send_message.assert_called_once_with('Invalid item invalid_item')


def test_action_show_item(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.action_show_item()

        mock_send_message.assert_called_once_with('word1')
        assert flashcard_bot.answer == 'word2'
        assert flashcard_bot.pending_item


def test_process_answer_correct(flashcard_bot):
    flashcard_bot.pending_item = True
    flashcard_bot.answer = 'word2'
    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.process_answer('word2')
        mock_send_message.assert_called_once_with('OK!')
        assert not flashcard_bot.pending_item
        assert flashcard_bot.answer is None
        assert flashcard_bot.attempt == 0


def test_process_answer_incorrect(flashcard_bot):
    flashcard_bot.answer = 'word2'

    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.process_answer('wrong_answer')

        mock_send_message.assert_called_once_with('ERROR - Current attempt 1')
        assert flashcard_bot.attempt == 1
        assert not flashcard_bot.pending_item


def test_process_answer_max_attempts(flashcard_bot):
    flashcard_bot.answer = 'word2'
    flashcard_bot.attempt = 2

    flashcard_bot.process_answer('wrong_answer')
    assert flashcard_bot.attempt == 0
    assert not flashcard_bot.pending_item


def test_process_message(flashcard_bot):
    # Test when there is no pending item
    flashcard_bot.pending_item = False

    # Case 1: Message without delimiter
    message = 'show'
    with patch.object(flashcard_bot,
                      'process_action') as mock_process_action:
        flashcard_bot.process_message(message)
        assert mock_process_action.call_count == 1
        flashcard_bot.process_action.assert_called_once_with('show', None)
    # Case 2: Message with delimiter
    message = 'new:item'
    with patch.object(flashcard_bot, 'process_action') as mock_process_action:
        flashcard_bot.process_message(message)
        assert mock_process_action.call_count == 1
        flashcard_bot.process_action.assert_called_once_with('new', 'item')
    # Test when there is a pending item
    flashcard_bot.pending_item = True

    # Case 3: Message with pending item
    message = 'answer'
    with patch.object(flashcard_bot, 'process_answer') as mock_process_answer:
        with patch.object(flashcard_bot,
                          'process_action') as mock_process_action:
            flashcard_bot.process_message(message)
            # process_answer should be called with the correct parameter
            mock_process_answer.assert_called_once_with('answer')
            # process_action should not be called
            assert mock_process_action.call_count == 0


def test_read_config():
    config = read_config('config/template.toml')
    assert config['Telegram']['API_KEY'] == "<YOUR_API_KEY>"
