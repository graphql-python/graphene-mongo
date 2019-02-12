import graphene
import mongoengine

from graphene import (
    Dynamic, Node
)

from py.test import raises

from .models import (
    Article, Editor, EmbeddedArticle, Player, Reporter,
    ProfessorMetadata, ProfessorVector,
    Publisher)
from .. import registry
from ..converter import convert_mongoengine_field
from ..fields import MongoengineConnectionField
from ..types import MongoengineObjectType


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


def test_sould_int_convert_int():
    assert_conversion(mongoengine.IntField, graphene.Int)


def test_sould_long_convert_int():
    assert_conversion(mongoengine.LongField, graphene.Int)


def test_should_object_id_convert_id():
    assert_conversion(mongoengine.ObjectIdField, graphene.ID)


def test_should_boolean_convert_boolean():
    assert_conversion(mongoengine.BooleanField, graphene.Boolean)


def test_should_decimal_convert_float():
    assert_conversion(mongoengine.DecimalField, graphene.Float)


def test_should_float_convert_float():
    assert_conversion(mongoengine.FloatField, graphene.Float)


def test_should_datetime_convert_datetime():
    assert_conversion(mongoengine.DateTimeField, graphene.DateTime)


def test_should_dict_convert_json():
    assert_conversion(mongoengine.DictField, graphene.JSONString)


def test_should_map_convert_json():
    assert_conversion(mongoengine.MapField, graphene.JSONString, field=mongoengine.StringField())


def test_should_point_convert_field():
    graphene_type = convert_mongoengine_field(mongoengine.PointField())
    assert isinstance(graphene_type, graphene.Field)
    assert isinstance(graphene_type.type.type, graphene.String)
    assert isinstance(graphene_type.type.coordinates, graphene.List)


def test_should_multipolygon_convert_field():
    graphene_type = convert_mongoengine_field(mongoengine.MultiPolygonField())
    assert isinstance(graphene_type, graphene.Field)
    assert isinstance(graphene_type.type.type, graphene.String)
    assert isinstance(graphene_type.type.coordinates, graphene.List)


def test_should_field_convert_list():
    assert_conversion(mongoengine.ListField, graphene.List, field=mongoengine.StringField())


def test_should_reference_convert_dynamic():

    class E(MongoengineObjectType):

        class Meta:
            model = Editor
            interfaces = (Node,)

    dynamic_field = convert_mongoengine_field(
        EmbeddedArticle._fields['editor'], E._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, graphene.Field)
    assert graphene_type.type == E


def test_should_lazy_reference_convert_dynamic():

    class P(MongoengineObjectType):

        class Meta:
            model = Publisher
            interfaces = (Node,)

    dynamic_field = convert_mongoengine_field(
        Editor._fields['company'], P._meta.registry)

    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, graphene.Field)
    assert graphene_type.type == P


def test_should_embedded_convert_dynamic():

    class PM(MongoengineObjectType):

        class Meta:
            model = ProfessorMetadata
            interfaces = (Node,)

    dynamic_field = convert_mongoengine_field(
        ProfessorVector._fields['metadata'], PM._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, graphene.Field)
    assert graphene_type.type == PM


def test_should_convert_none():
    registry.reset_global_registry()
    dynamic_field = convert_mongoengine_field(
        EmbeddedArticle._fields['editor'], registry.get_global_registry())
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert graphene_type is None


def test_should_convert_none_lazily():
    registry.reset_global_registry()
    dynamic_field = convert_mongoengine_field(
        Editor._fields['company'], registry.get_global_registry())
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert graphene_type is None


def test_should_list_of_reference_convert_list():

    class A(MongoengineObjectType):

        class Meta:
            model = Article

    graphene_field = convert_mongoengine_field(
        Reporter._fields['articles'], A._meta.registry)
    assert isinstance(graphene_field, graphene.List)
    dynamic_field = graphene_field.get_type()
    assert dynamic_field._of_type == A


def test_should_list_of_embedded_convert_list():

    class E(MongoengineObjectType):

        class Meta:
            model = EmbeddedArticle

    graphene_field = convert_mongoengine_field(
        Reporter._fields['embedded_articles'], E._meta.registry)
    assert isinstance(graphene_field, graphene.List)
    dynamic_field = graphene_field.get_type()
    assert dynamic_field._of_type == E


def test_should_embedded_list_convert_list():

    class E(MongoengineObjectType):

        class Meta:
            model = EmbeddedArticle

    graphene_field = convert_mongoengine_field(
        Reporter._fields['embedded_list_articles'], E._meta.registry)
    assert isinstance(graphene_field, graphene.List)
    dynamic_field = graphene_field.get_type()
    assert dynamic_field._of_type == E


def test_should_self_reference_convert_dynamic():

    class P(MongoengineObjectType):

        class Meta:
            model = Player
            interfaces = (Node,)

    dynamic_field = convert_mongoengine_field(
        Player._fields['opponent'], P._meta.registry)
    assert isinstance(dynamic_field, Dynamic)
    graphene_type = dynamic_field.get_type()
    assert isinstance(graphene_type, graphene.Field)
    assert graphene_type.type == P

    graphene_field = convert_mongoengine_field(
        Player._fields['players'], P._meta.registry)
    assert isinstance(graphene_field, MongoengineConnectionField)


def test_should_list_of_self_reference_convert_list():

    class A(MongoengineObjectType):

        class Meta:
            model = Article

    class P(MongoengineObjectType):

        class Meta:
            model = Player

    graphene_field = convert_mongoengine_field(
        Player._fields['players'], P._meta.registry)
    assert isinstance(graphene_field, graphene.List)
    dynamic_field = graphene_field.get_type()
    assert dynamic_field._of_type == P


def test_should_description_convert_common_metadata():

    class A(MongoengineObjectType):

        class Meta:
            model = Article

    headline_field = convert_mongoengine_field(
        Article._fields['headline'], A._meta.registry
    )
    assert headline_field.kwargs['description'] == "The article headline."

    pubDate_field = convert_mongoengine_field(
        Article._fields['pub_date'], A._meta.registry
    )
    assert pubDate_field.kwargs['description'] == "Publication Date\nThe date of first press."

    firstName_field = convert_mongoengine_field(
        Editor._fields['first_name'], A._meta.registry
    )
    assert firstName_field.kwargs['description'] == "Editor's first name.\n(fname)"

    metadata_field = convert_mongoengine_field(
        Editor._fields['metadata'], A._meta.registry
    )
    assert metadata_field.kwargs['description'] == "Arbitrary metadata."


def test_should_description_convert_reference_metadata():

    class A(MongoengineObjectType):

        class Meta:
            model = Article

    class E(MongoengineObjectType):

        class Meta:
            model = Editor

    editor_field = convert_mongoengine_field(
        Article._fields['editor'], A._meta.registry
    ).get_type()
    assert editor_field.description == "An Editor of a publication."
