import graphene
import mongoengine
import pytest

from py.test import raises

from ..converter import convert_mongoengine_field

def assert_conversion(mongoengine_field, graphene_field, *args, **kwargs):
    field = mongoengine_field(*args, **kwargs)
    graphene_type = convert_mongoengine_field(field)
    assert isinstance(graphene_type, graphene_field)
    field = graphene_type.Field()
    return field

def test_should_unknown_mongoengine_field_raise_exception():
    with raises(Exception) as excinfo:
        convert_mongoengine_field(None)
    assert "Don't know how to convert the MongoEngine field" in str(excinfo)


def test_should_email_convert_string():
    assert_conversion(mongoengine.EmailField, graphene.String)


def test_should_string_convert_string():
    assert_conversion(mongoengine.StringField, graphene.String)


def test_should_url_convert_string():
    assert_conversion(mongoengine.URLField, graphene.String)


def test_should_uuid_convert_id():
    assert_conversion(mongoengine.UUIDField, graphene.ID)


def test_should_object_id_convert_id():
    assert_conversion(mongoengine.ObjectIdField, graphene.ID)


def test_should_boolean_convert_non_null():
    assert_conversion(mongoengine.BooleanField, graphene.NonNull)


def test_should_decimal_convert_float():
    assert_conversion(mongoengine.DecimalField, graphene.Float)


def test_should_float_convert_float():
    assert_conversion(mongoengine.FloatField, graphene.Float)


def test_should_date_convert_string():
    assert_conversion(mongoengine.DateTimeField, graphene.String)


def test_should_dict_convert_json():
    assert_conversion(mongoengine.DictField, graphene.JSONString)


#def test_should_convert_map_to_json():
#    assert_conversion(mongoengine.MapField, graphene.JSONString)


def test_should_postgres_array_convert_list():
    assert_conversion(mongoengine.ListField, graphene.List, field=mongoengine.StringField())

