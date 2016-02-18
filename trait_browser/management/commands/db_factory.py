"""
Factory functions to produce fake data for testing populate_source_traits.py
"""

from faker import Faker

fake = Faker()

def fake_row_dict():
    """Return a fake dictionary, similar to what would be returned by a
    mysql cursor object with dictionary=True. This dict contains one of
    each type of data that could be returned from a database."""
    return {
        'text': fake.text(),
        'word': fake.word(),
        'bytearray_word': bytearray(fake.word(), 'utf-8'),
        'date': fake.date_time(),
        'company': fake.company(),
        'int': fake.pyint(),
        'none': None,
        'empty_string': ''
    }