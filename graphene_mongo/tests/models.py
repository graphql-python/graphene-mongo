import mongoengine
from datetime import datetime
from mongoengine.fields import (
    DateTimeField, EmailField, EmbeddedDocumentField,
    FloatField, EmbeddedDocumentListField, ListField, LazyReferenceField,
    MapField, MultiPolygonField, PointField, PolygonField,
    ReferenceField, StringField,
)

mongoengine.connect('graphene-mongo-test', host='mongomock://localhost', alias='default')


class Publisher(mongoengine.Document):

    meta = {'collection': 'test_publisher'}
    name = mongoengine.StringField()

    @property
    def legal_name(self):
        return self.name + " Inc."

    def bad_field(self):
        return None


class Editor(mongoengine.Document):
    """
    An Editor of a publication.
    """

    meta = {'collection': 'test_editor'}
    id = mongoengine.StringField(primary_key=True)
    first_name = mongoengine.StringField(required=True, help_text="Editor's first name.", db_field='fname')
    last_name = mongoengine.StringField(required=True, help_text="Editor's last name.")
    metadata = mongoengine.MapField(field=mongoengine.StringField(), help_text="Arbitrary metadata.")
    company = mongoengine.LazyReferenceField(Publisher)


class Article(mongoengine.Document):

    meta = {'collection': 'test_article'}
    headline = mongoengine.StringField(required=True, help_text="The article headline.")
    pub_date = mongoengine.DateTimeField(
        default=datetime.now,
        verbose_name="publication date",
        help_text="The date of first press.")
    editor = mongoengine.ReferenceField(Editor)
    reporter = mongoengine.ReferenceField('Reporter')


class EmbeddedArticle(mongoengine.EmbeddedDocument):

    meta = {'collection': 'test_embedded_article'}
    headline = mongoengine.StringField(required=True)
    pub_date = mongoengine.DateTimeField(default=datetime.now)
    editor = mongoengine.ReferenceField(Editor)
    reporter = mongoengine.ReferenceField('Reporter')


class Reporter(mongoengine.Document):

    meta = {'collection': 'test_reporter'}
<<<<<<< HEAD
    id = StringField(primary_key=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField()
    awards = ListField(StringField())
    articles = ListField(ReferenceField(Article))
    embedded_articles = ListField(EmbeddedDocumentField(EmbeddedArticle))
    embedded_list_articles = EmbeddedDocumentListField(EmbeddedArticle)
    id = StringField(primary_key=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField()
    articles = ListField(ReferenceField(Article))
    embedded_articles = ListField(EmbeddedDocumentField(EmbeddedArticle))
    embedded_list_articles = EmbeddedDocumentListField(EmbeddedArticle)
    awards = ListField(StringField())


class Player(mongoengine.Document):

    meta = {'collection': 'test_player'}
    first_name = mongoengine.StringField(required=True)
    last_name = mongoengine.StringField(required=True)
    opponent = mongoengine.ReferenceField('Player')
    players = mongoengine.ListField(mongoengine.ReferenceField('Player'))
    articles = mongoengine.ListField(mongoengine.ReferenceField('Article'))
    embedded_list_articles = mongoengine.EmbeddedDocumentListField(EmbeddedArticle)


class Parent(mongoengine.Document):

    meta = {
        'collection': 'test_parent',
        'allow_inheritance': True
    }
    bar = mongoengine.StringField()
    loc = mongoengine.MultiPolygonField()
    # reference = GenericReferenceField()


class CellTower(mongoengine.Document):

    meta = {
        'collection': 'test_cell_tower',
    }
    code = StringField()
    base = PolygonField()
    coverage_area = MultiPolygonField()


class Child(Parent):

    meta = {'collection': 'test_child'}
    baz = mongoengine.StringField()
    loc = mongoengine.PointField()


class ProfessorMetadata(mongoengine.EmbeddedDocument):

    meta = {'collection': 'test_professor_metadata'}
    id = mongoengine.StringField(primary_key=False)
    first_name = mongoengine.StringField()
    last_name = mongoengine.StringField()
    departments = mongoengine.ListField(mongoengine.StringField())


class ProfessorVector(mongoengine.Document):

    meta = {'collection': 'test_professor_vector'}
    vec = mongoengine.ListField(mongoengine.FloatField())
    metadata = mongoengine.EmbeddedDocumentField(ProfessorMetadata)


class ParentWithRelationship(mongoengine.Document):

    meta = {'collection': 'test_parent_reference'}
    before_child = mongoengine.ListField(
        mongoengine.ReferenceField('ChildRegisteredBefore'))
    after_child = mongoengine.ListField(
        mongoengine.ReferenceField('ChildRegisteredAfter'))
    name = mongoengine.StringField()


class ChildRegisteredBefore(mongoengine.Document):

    meta = {'collection': 'test_child_before_reference'}
    parent = mongoengine.ReferenceField(ParentWithRelationship)
    name = mongoengine.StringField()


class ChildRegisteredAfter(mongoengine.Document):

    meta = {'collection': 'test_child_after_reference'}
    parent = mongoengine.ReferenceField(ParentWithRelationship)
    name = mongoengine.StringField()


class ErroneousModel(mongoengine.Document):
    meta = {'collection': 'test_colliding_objects_model'}

    objects = mongoengine.ListField(mongoengine.StringField())
