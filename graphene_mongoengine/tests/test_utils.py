import pytest
from mongoengine import Document


from ..utils import (
    get_model_fields, is_valid_mongoengine_model
)
from .models import Reporter

def test_get_model_fields_no_duplication():
    reporter_fields = get_model_fields(Reporter)
    reporter_name_set = set(reporter_fields)
    assert len(reporter_fields) == len(reporter_name_set)


def test_is_valid_mongoengine_mode():
    assert is_valid_mongoengine_model(Reporter)

