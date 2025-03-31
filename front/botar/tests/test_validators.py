import pytest
from utils.validators import is_valid_full_name, normalize_name

@pytest.mark.parametrize("name,expected", [
    ("Иван Иванов", True),
    ("Петров Илья Сергеевич", True),      # multiple words should be fine (>=2 words)
    ("Ivan Ivanov", False),              # contains Latin letters
    ("Иван", False),                     # only one word
    ("Иван123 Иванов", False),           # contains digits, thus not purely letters
    ("Иван Иванов ", True),              # trailing space is okay after strip
])
def test_is_valid_full_name(name, expected):
    assert is_valid_full_name(name) == expected

def test_normalize_name():
    assert normalize_name(" Иванов Иван\n") == "иванов иван"
    assert normalize_name("Ёжиков Ёж") == "ежиков еж"
