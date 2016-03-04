"""Factory functions to produce fake data for testing trait_browser's populate_source_traits management command."""

from faker import Faker


fake = Faker()


def fake_row_dict():
    """Make fake sql table data (factory).
    
    Generate a fake dictionary, similar to what would be returned by a
    mysql cursor object with dictionary=True. This dict contains one of
    each type of data that could be returned from a database.
    
    Returns:
        a dict with data of several types
        
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