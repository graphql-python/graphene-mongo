from graphene import Field, Int, Interface, ObjectType
from graphene.relay import Node, is_node

from .. import registry
from ..types import MongoengineObjectType
from .models import Article
from .models import Reporter

registry.reset_global_registry()


class Human(MongoengineObjectType):

    pub_date = Int()

    class Meta:
        model = Article
        registry = registry.get_global_registry()
        interfaces = (Node,)


class Character(MongoengineObjectType):
    class Meta:
        model = Reporter
        registry = registry.get_global_registry()


def test_mongoengine_interface():
    assert issubclass(Node, Interface)
    assert issubclass(Node, Node)


def test_objecttype_registered():
    assert issubclass(Character, ObjectType)
    assert Character._meta.model == Reporter
    assert set(
        Character._meta.fields.keys()) == set([
        'id',
        'first_name',
        'last_name',
        'email',
        'articles',
        'awards'])


def test_node_replacedfield():
    idfield = Human._meta.fields['pub_date']
    assert isinstance(idfield, Field)
    assert idfield.type == Int


def test_object_type():
    assert issubclass(Human, ObjectType)
    assert set(Human._meta.fields.keys()) == set(['id', 'headline', 'pub_date', 'editor', 'reporter']
)
    assert is_node(Human)


def with_local_registry(func):
    def inner(*args, **kwargs):
        old = registry.get_global_registry()
        registry.reset_global_registry()
        try:
            retval = func(*args, **kwargs)
        except Exception as e:
            registry.registry = old
            raise e
        else:
            registry.registry = old
            return retval
    return inner


@with_local_registry
def test_mongoengine_objecttype_only_fields():
    class A(MongoengineObjectType):
        class Meta:
            model = Article
            only_fields = ('headline')


    fields = set(A._meta.fields.keys())
    assert fields == set(['headline'])


@with_local_registry
def test_mongoengine_objecttype_exclude_fields():
    class A(MongoengineObjectType):
        class Meta:
            model = Article
            exclude_fields = ('headline')

    assert 'headline' not in list(A._meta.fields.keys())

