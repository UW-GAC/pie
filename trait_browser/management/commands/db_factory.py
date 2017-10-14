"""Factory functions to produce fake data for testing trait_browser's populate_source_traits management command."""

from faker import Faker
from mysql.connector import FieldType


fake = Faker()


MYSQL_TYPES = {FieldType.get_info(el): el for el in FieldType.get_binary_types() +
               FieldType.get_number_types() +
               FieldType.get_string_types() +
               FieldType.get_timestamp_types()}


def fake_row_dict():
    """Make fake sql table data (factory).

    Generate a fake dictionary, similar to what would be returned by a
    mysql cursor object with dictionary=True. This dict contains one of
    each type of data that could be returned from a database.

    Returns:
        tuple of (row_dict, cursor_description)
        row_dict: a dict with data of several types
        cursor_description: tuple mimicing the cursor.description values from MySQL connector

        dict keys:
            text
            word
            bytearray_word
            date
            company
            int
            none
            empty_string
    """
    return (
        {'text': fake.text(),
         'word': fake.word(),
         'bytearray_word': bytearray(fake.word(), 'utf-8'),
         'timestamp': fake.date_time(),
         'datetime': fake.date_time(),
         'company': fake.company(),
         'int': fake.pyint(),
         'boolean': int(fake.pybool()),
         'null_string': None,
         'empty_string': ''},
        {'text': MYSQL_TYPES['BLOB'],
         'word': MYSQL_TYPES['VARCHAR'],
         'bytearray_word': MYSQL_TYPES['ENUM'],
         'timestamp': MYSQL_TYPES['TIMESTAMP'],
         'datetime': MYSQL_TYPES['DATETIME'],
         'company': MYSQL_TYPES['VARCHAR'],
         'int': MYSQL_TYPES['INT24'],
         'boolean': MYSQL_TYPES['TINY'],
         'null_string': MYSQL_TYPES['VARCHAR'],
         'empty_string': MYSQL_TYPES['VARCHAR']}
    )
