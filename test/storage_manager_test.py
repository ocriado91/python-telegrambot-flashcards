#!/usr/bin/env python3

import os
import pytest

from storage_manager import StorageManager, StorageManagerException

def test_new_item():
    '''
    Check add a new item into DB
    '''

    storage_manager = StorageManager(database="test_flashcard.db")

    # Insert first pair
    storage_manager.insert_item("text", "test1", "test2")

    # If we try to insert again the same target field, the
    # StorageManager raises the custom exception due to
    # a SQL integrity error
    with pytest.raises(StorageManagerException):
        storage_manager.insert_item("text", "test1", "test3")

def test_successfully_close_connection():
    '''
    Check close connection DB
    '''

    storage_manager = StorageManager(database="test_flashcard.db")
    storage_manager.close_connection()
    with pytest.raises(StorageManagerException):
        storage_manager.insert_item("text", "testA", "testB")


@pytest.fixture(scope='session', autouse=True)
def remove_test_db():
    '''
    Remove database after execute tests
    '''
    yield
    os.remove("test_flashcard.db")