import mongoengine
from datetime import datetime
from mongoengine import fields

mongoengine.connect('graphene-mongo-test', host='mongomock://localhost', alias='default')


class Publisher(mongoengine.Document):

    meta = {'collection': 'test_publisher'}
    name = fields.StringField()

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
    id = fields.StringField(primary_key=True)
    first_name = fields.StringField(required=True, help_text="Editor's first name.", db_field='fname')
    last_name = fields.StringField(required=True, help_text="Editor's last name.")
    metadata = fields.MapField(field=fields.StringField(), help_text="Arbitrary metadata.")
    company = fields.LazyReferenceField(Publisher)


class Article(mongoengine.Document):

    meta = {'collection': 'test_article'}
    headline = fields.StringField(required=True, help_text="The article headline.")
    pub_date = fields.DateTimeField(
        default=datetime.now,
        verbose_name="publication date",
        help_text="The date of first press.")
    editor = fields.ReferenceField(Editor)
    reporter = fields.ReferenceField('Reporter')


class EmbeddedArticle(mongoengine.EmbeddedDocument):

    meta = {'collection': 'test_embedded_article'}
    headline = fields.StringField(required=True)
    pub_date = fields.DateTimeField(default=datetime.now)
    editor = fields.ReferenceField(Editor)
    reporter = fields.ReferenceField('Reporter')


class Reporter(mongoengine.Document):

    meta = {'collection': 'test_reporter'}
    id = fields.StringField(primary_key=True)
    first_name = fields.StringField(required=True)
    last_name = fields.StringField(required=True)
    email = fields.EmailField()
    awards = fields.ListField(fields.StringField())
    articles = fields.ListField(fields.ReferenceField(Article))
    embedded_articles = fields.ListField(fields.EmbeddedDocumentField(EmbeddedArticle))
    embedded_list_articles = fields.EmbeddedDocumentListField(EmbeddedArticle)
    id = fields.StringField(primary_key=True)
    first_name = fields.StringField(required=True)
    last_name = fields.StringField(required=True)
    email = fields.EmailField()
    awards = fields.ListField(fields.StringField())
    articles = fields.ListField(fields.ReferenceField(Article))
    embedded_articles = fields.ListField(fields.EmbeddedDocumentField(EmbeddedArticle))
    embedded_list_articles = fields.EmbeddedDocumentListField(EmbeddedArticle)


class Player(mongoengine.Document):

    meta = {'collection': 'test_player'}
    first_name = fields.StringField(required=True)
    last_name = fields.StringField(required=True)
    opponent = fields.ReferenceField('Player')
    players = fields.ListField(fields.ReferenceField('Player'))
    articles = fields.ListField(fields.ReferenceField('Article'))
    embedded_list_articles = fields.EmbeddedDocumentListField(EmbeddedArticle)


class Parent(mongoengine.Document):

    meta = {
        'collection': 'test_parent',
        'allow_inheritance': True
    }
    bar = fields.StringField()
    loc = fields.MultiPolygonField()
    generic_reference = fields.GenericReferenceField(
        choices=[Article, Reporter, ]
    )


class CellTower(mongoengine.Document):

    meta = {
        'collection': 'test_cell_tower',
    }
    code = fields.StringField()
    base = fields.PolygonField()
    coverage_area = fields.MultiPolygonField()


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
