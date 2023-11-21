from pytest import raises

from graphene import Field, Int, Interface, ObjectType
from graphene.relay import Node, is_node

from .. import registry
from ..types import MongoengineObjectType, MongoengineObjectTypeOptions
from .models import Article, EmbeddedArticle, Reporter
from .models import Parent, Child
from .utils import with_local_registry

registry.reset_global_registry()


class Human(MongoengineObjectType):
    pub_date = Int()

    class Meta:
        model = Article
        registry = registry.get_global_registry()
        interfaces = (Node,)


class Being(MongoengineObjectType):
    class Meta:
        model = EmbeddedArticle
        interfaces = (Node,)


class Character(MongoengineObjectType):
    class Meta:
        model = Reporter
        registry = registry.get_global_registry()


class Dad(MongoengineObjectType):
    class Meta:
        model = Parent
        registry = registry.get_global_registry()


class Son(MongoengineObjectType):
    class Meta:
        model = Child
        registry = registry.get_global_registry()


def test_mongoengine_interface():
    assert issubclass(Node, Interface)
    assert issubclass(Node, Node)


def test_objecttype_registered():
    assert issubclass(Character, ObjectType)
    assert Character._meta.model == Reporter
    assert set(Character._meta.fields.keys()) == set(
        [
            "id",
            "first_name",
            "last_name",
            "email",
            "embedded_articles",
            "embedded_list_articles",
            "articles",
            "awards",
            "generic_reference",
            "generic_embedded_document",
            "generic_references",
        ]
    )


def test_mongoengine_inheritance():
    assert issubclass(Son._meta.model, Dad._meta.model)


def test_node_replacedfield():
    idfield = Human._meta.fields["pub_date"]
    assert isinstance(idfield, Field)
    assert idfield.type == Int


def test_object_type():
    assert issubclass(Human, ObjectType)
    assert set(Human._meta.fields.keys()) == set(
        ["id", "headline", "pub_date", "editor", "reporter"]
    )
    assert is_node(Human)


def test_should_raise_if_no_model():
    with raises(Exception) as excinfo:

        class Human1(MongoengineObjectType):
            pass

    assert "valid Mongoengine Model" in str(excinfo.value)


def test_should_raise_if_model_is_invalid():
    with raises(Exception) as excinfo:

        class Human2(MongoengineObjectType):
            class Meta:
                model = 1

    assert "valid Mongoengine Model" in str(excinfo.value)


@with_local_registry
def test_mongoengine_objecttype_only_fields():
    class A(MongoengineObjectType):
        class Meta:
            model = Article
            only_fields = "headline"

    fields = set(A._meta.fields.keys())
    assert fields == set(["headline"])


@with_local_registry
def test_mongoengine_objecttype_exclude_fields():
    class A(MongoengineObjectType):
        class Meta:
            model = Article
            exclude_fields = "headline"

    assert "headline" not in list(A._meta.fields.keys())


@with_local_registry
def test_mongoengine_objecttype_order_by():
    class A(MongoengineObjectType):
        class Meta:
            model = Article
            order_by = "some_order_by_statement"

    assert "some_order_by_statement" not in list(A._meta.fields.keys())


@with_local_registry
def test_passing_meta_when_subclassing_mongoengine_objecttype():
    class TypeSubclassWithBadOptions(MongoengineObjectType):
        class Meta:
            abstract = True

        @classmethod
        def __init_subclass_with_meta__(cls, **kwargs):
            _meta = ["hi"]
            super(TypeSubclassWithBadOptions, cls).__init_subclass_with_meta__(
                _meta=_meta, **kwargs
            )

    with raises(Exception) as einfo:

        class A(TypeSubclassWithBadOptions):
            class Meta:
                model = Article

    assert "instance of MongoengineGenericObjectTypeOptions" in str(einfo.value)

    class TypeSubclass(MongoengineObjectType):
        class Meta:
            abstract = True

        @classmethod
        def __init_subclass_with_meta__(cls, some_subclass_attr=None, **kwargs):
            _meta = MongoengineObjectTypeOptions(cls)
            _meta.some_subclass_attr = some_subclass_attr
            super(TypeSubclass, cls).__init_subclass_with_meta__(_meta=_meta, **kwargs)

    class B(TypeSubclass):
        class Meta:
            model = Article
            some_subclass_attr = "someval"

    assert hasattr(B._meta, "some_subclass_attr")
    assert B._meta.some_subclass_attr == "someval"
