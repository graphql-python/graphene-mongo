import pytest
from mongoengine import Document


from ..utils import (
    get_model_fields, is_valid_mongoengine_model
)
from .models import Article, Reporter, Child


def test_get_model_fields_no_duplication():
    reporter_fields = get_model_fields(Reporter)
    reporter_name_set = set(reporter_fields)
    assert len(reporter_fields) == len(reporter_name_set)


def test_get_model_relation_fields():
    article_fields = get_model_fields(Article)
    assert all(field in set(article_fields) for field in ['editor', 'reporter'])


def test_get_base_model_fields():
    child_fields = get_model_fields(Child)
    assert all(field in set(child_fields) for field in ['bar', 'baz'])

def test_is_valid_mongoengine_mode():
    assert is_valid_mongoengine_model(Reporter)

