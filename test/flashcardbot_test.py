import pytest
from unittest.mock import patch, Mock
from flashcard import FlashCardBot, read_config


@pytest.fixture
def flashcard_bot():
    config = {'Telegram':
              {'API_KEY': 'api_key'}}
    return FlashCardBot(config, database='test_data.db', max_attempts=3)


@pytest.fixture
def mock_cursor():
    # Mock the database cursor for the test
    rows = [
        # Sample data for the test rows
        # Adjust the data according to your needs
        (1, '2022/05/20T12:00:00', 'Hello', 'Hola', 0,
         0, 0, '2023/04/12T19:00:00', 'text'),
        (2, '2023/05/20T12:00:00', 'Hello', 'Hola', 1,
         0, 0, '2023/04/12T12:00:00', 'text'),
        (3, '2023/05/20T12:00:00', 'Hello', 'Hola', 2,
         0, 0, '2023/04/06T12:00:00', 'text'),
        (4, '2023/05/20T12:00:00', 'Hello', 'Hola', 3,
         0, 0, '2023/04/17t12:00:00', 'text')
    ]
    mock_cursor = Mock()
    mock_cursor.execute.return_value.fetchall.return_value = rows
    return mock_cursor


def test_process_action_new(flashcard_bot):
    with patch.object(flashcard_bot,
                      'action_new_item') as mock_action_new_item:
        flashcard_bot.process_action('new', 'word1 - word2')
        mock_action_new_item.assert_called_once_with('word1 - word2')


def test_process_action_remove(flashcard_bot):
    with patch.object(flashcard_bot,
                      'action_remove_item') as mock_action_remove_item:
        flashcard_bot.process_action('remove', 'word1 - word3')
        mock_action_remove_item.assert_called_once_with('word1 - word3')


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
                      'send_message') as mock_send_message, \
        patch.object(flashcard_bot.telegrambot,
                     'get_chat_id') as _:
        # Test adding a new item
        flashcard_bot.action_new_item('word1 - word2')
        # Verify that the item is added to the database
        flashcard_bot.cursor.execute('SELECT * FROM items WHERE target=?',
                                     ('word1',))
        result = flashcard_bot.cursor.fetchone()
        assert result is not None
        assert result[2] == 'word1'
        assert result[3] == 'word2'
        msg = 'Successfully added new item word1 - word2'
        mock_send_message.assert_called_once_with(msg)

        # Test adding a duplicate item
        flashcard_bot.action_new_item('word1 - word2')

        # Verify that the duplicate item is not added
        flashcard_bot.cursor.execute('''SELECT COUNT(*)
                                    FROM items WHERE target=?''', ('word1',))
        result = flashcard_bot.cursor.fetchone()
        # Should still have only 1 item with target 'word1'
        assert result[0] == 1


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
        assert flashcard_bot.target[2] == 'word1'
        assert flashcard_bot.target[3] == 'word2'
        assert flashcard_bot.pending_item


def test_process_answer_correct(flashcard_bot):
    flashcard_bot.target = [1, '2020', 'word1', 'word2', 0, 0, 0]

    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.process_answer('word2')

        mock_send_message.assert_called_once_with('OK!')
        assert flashcard_bot.attempt == 0
        assert not flashcard_bot.pending_item


def test_action_remove_item_correct(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.action_remove_item('word1 - word2')
        mock_send_message.assert_called_once_with('Successfully removed items')


def test_action_remove_item_invalid(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.action_remove_item('word1 - word2')
        msg = 'Item word1 - word2 not found in database'
        mock_send_message.assert_called_once_with(msg)


def test_action_show_item_empty(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.action_show_item()
        mock_send_message.assert_called_once_with('No items found in database')


def test_process_answer_incorrect(flashcard_bot):
    flashcard_bot.target = [1, '2020', 'word1', 'word2', 0, 0, 0]

    with patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.process_answer('wrong_answer')

        mock_send_message.assert_called_once_with('ERROR - Current attempt 1')
        assert flashcard_bot.attempt == 1
        assert not flashcard_bot.pending_item


def test_process_answer_max_attempts(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot,
                      'get_chat_id') as _:
        flashcard_bot.target = [1, '2020', 'word1', 'word2', 0, 0, 0]
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

@patch('sys.exit')
def test_read_config_with_invalid_file(mock_exit):
    mock_exit.side_effect = FileNotFoundError()
    with pytest.raises(FileNotFoundError):
        read_config('configfile')

def test_scheduler(mock_cursor, flashcard_bot):

    flashcard_bot.cursor = mock_cursor
    # Mock the action_show_item method
    with patch.object(flashcard_bot, 'action_show_item') as \
         mock_action_show_item:
        # Call the scheduler method
        flashcard_bot.scheduler()
        # Assert number of calls to show item action
        assert mock_action_show_item.call_count == 4


def test_process_correct_answer(flashcard_bot):

    with patch.object(flashcard_bot.telegrambot, 'get_chat_id') as _,\
         patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.target = [1, '2020', 'word1', 'word2', 0, 160, 0]
        flashcard_bot.process_correct_answer()
        msg = 'Modified word1 from Daily to Weekly'
        mock_send_message.assert_called_with(msg)

        flashcard_bot.target = [1, '2020', 'word1', 'word2', 1, 160, 0]
        flashcard_bot.process_correct_answer()
        msg = 'Modified word1 from Weekly to Bi-Weekly'
        mock_send_message.assert_called_with(msg)

        flashcard_bot.target = [1, '2020', 'word1', 'word2', 2, 160, 0]
        flashcard_bot.process_correct_answer()
        msg = 'Modified word1 from Bi-Weekly to Monthly'
        mock_send_message.assert_called_with(msg)


def test_process_wrong_answer(flashcard_bot):

    with patch.object(flashcard_bot.telegrambot, 'get_chat_id') as _,\
         patch.object(flashcard_bot.telegrambot,
                      'send_message') as mock_send_message:
        flashcard_bot.target = [1, '2020', 'word1', 'word2', 3, 0, 160]
        flashcard_bot.process_wrong_answer()
        msg = 'Modified word1 from Monthly to Bi-Weekly'
        mock_send_message.assert_called_with(msg)

        flashcard_bot.target = [1, '2020', 'word1', 'word2', 2, 0, 160]
        flashcard_bot.process_wrong_answer()
        msg = 'Modified word1 from Bi-Weekly to Weekly'
        mock_send_message.assert_called_with(msg)

        flashcard_bot.target = [1, '2020', 'word1', 'word2', 1, 0, 160]
        flashcard_bot.process_wrong_answer()
        msg = 'Modified word1 from Weekly to Daily'
        mock_send_message.assert_called_with(msg)


def test_action_show_item_photo(flashcard_bot):
    with patch.object(flashcard_bot.telegrambot, 'get_chat_id') as _,\
            patch.object(flashcard_bot.telegrambot,
                         'send_photo') as mock_send_photo:

        row = (4, '2023/05/20T12:00:00', 'word1', 'word2', 3,
               0, 0, '2023/04/17t12:00:00', 'photo')
        flashcard_bot.action_show_item(row)

        mock_send_photo.assert_called_once_with('word1')
        assert flashcard_bot.target[2] == 'word1'
        assert flashcard_bot.target[3] == 'word2'
        assert flashcard_bot.pending_item


def test_process_photo(flashcard_bot):
    data = {'photo': [{'file_id': 33}],
            'caption': 'Fernando Alonso Winner!'}
    with patch.object(flashcard_bot.telegrambot, 'get_chat_id') as _,\
            patch.object(flashcard_bot.telegrambot,
                         'send_message') as mock_send_message:
        flashcard_bot.process_photo(data)
        mock_send_message.assert_called_with('Successfully added photo')


def test_process_photo_no_caption(flashcard_bot):
    data = {'photo': [{'file_id': 14}]}
    with patch.object(flashcard_bot.telegrambot, 'get_chat_id') as _,\
            patch.object(flashcard_bot.telegrambot,
                         'send_message') as mock_send_message:
        flashcard_bot.process_photo(data)
        mock_send_message.assert_called_with(
            'Please, insert a caption into the photo')
