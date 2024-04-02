#!/usr/bin/env python3

import os
import pytest

from storage_manager import StorageManager, StorageManagerException

def test_new_item():
    '''
    Check add a new item into DB
    '''

    # Initialize Storage Manager
    storage_manager = StorageManager(database="test_flashcard.db")

    # Insert first pair
    storage_manager.insert_item("text", "test1", "test2")

    # If we try to insert again the same target field, the
    # StorageManager raises the custom exception due to
    # a SQL integrity error
    with pytest.raises(StorageManagerException):
        storage_manager.insert_item("text", "test1", "test3")

def test_select_random_item():
    '''
    Test random selection of a item
    '''

    # Initialize Storage Manager
    storage_manager = StorageManager(database="test_flashcard_random.db")

    # Insert a new item
    storage_manager.insert_item("text", "testA", "testB")

    # Try to extract items
    item = storage_manager.select_random_item()
    assert item[0] == 1
    assert item[2] == "testA"
    assert item[3] == "testB"
    assert item[6] == "text"

def test_successfully_close_connection():
    '''
    Check close connection DB
    '''

    # Initialize Storage Manager
    storage_manager = StorageManager(database="test_flashcard.db")

    # Close connection
    storage_manager.close_connection()

    # Try to insert a item with the connection closed.
    # A StorageManagerException raises due to a sqlite3
    # ProgrammingError exception
    with pytest.raises(StorageManagerException):
        storage_manager.insert_item("text", "testA", "testB")

@pytest.fixture(scope='session', autouse=True)
def remove_test_db():
    '''
    Remove database after execute tests
    '''
    yield
    os.remove("test_flashcard.db")
    os.remove("test_flashcard_random.db")