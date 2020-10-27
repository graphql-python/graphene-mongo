import mongoengine
from datetime import datetime
from mongomock import gridfs

gridfs.enable_gridfs_integration()
mongoengine.connect(
    "graphene-mongo-test", host="mongomock://localhost", alias="default"
)
# mongoengine.connect('graphene-mongo-test', host='mongodb://localhost/graphene-mongo-dev')


class Publisher(mongoengine.Document):

    meta = {"collection": "test_publisher"}
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

    meta = {"collection": "test_editor"}
    id = mongoengine.StringField(primary_key=True)
    first_name = mongoengine.StringField(
        required=True, help_text="Editor's first name.", db_field="fname"
    )
    last_name = mongoengine.StringField(required=True, help_text="Editor's last name.")
    metadata = mongoengine.MapField(
        field=mongoengine.StringField(), help_text="Arbitrary metadata."
    )
    company = mongoengine.LazyReferenceField(Publisher)
    avatar = mongoengine.FileField()
    seq = mongoengine.SequenceField()


class Article(mongoengine.Document):

    meta = {"collection": "test_article"}
    headline = mongoengine.StringField(required=True, help_text="The article headline.")
    pub_date = mongoengine.DateTimeField(
        default=datetime.now,
        verbose_name="publication date",
        help_text="The date of first press.",
    )
    editor = mongoengine.ReferenceField(Editor)
    reporter = mongoengine.ReferenceField("Reporter")
    # Will not convert these fields cause no choices
    # generic_reference = mongoengine.GenericReferenceField()
    # generic_embedded_document = mongoengine.GenericEmbeddedDocumentField()


class EmbeddedArticle(mongoengine.EmbeddedDocument):

    meta = {"collection": "test_embedded_article"}
    headline = mongoengine.StringField(required=True)
    pub_date = mongoengine.DateTimeField(default=datetime.now)
    editor = mongoengine.ReferenceField(Editor)
    reporter = mongoengine.ReferenceField("Reporter")


class EmbeddedFoo(mongoengine.EmbeddedDocument):
    meta = {"collection": "test_embedded_foo"}
    bar = mongoengine.StringField()


class Reporter(mongoengine.Document):

    meta = {"collection": "test_reporter"}
    id = mongoengine.StringField(primary_key=True)
    first_name = mongoengine.StringField(required=True)
    last_name = mongoengine.StringField(required=True)
    email = mongoengine.EmailField()
    awards = mongoengine.ListField(mongoengine.StringField())
    articles = mongoengine.ListField(mongoengine.ReferenceField(Article))
    embedded_articles = mongoengine.ListField(
        mongoengine.EmbeddedDocumentField(EmbeddedArticle)
    )
    embedded_list_articles = mongoengine.EmbeddedDocumentListField(EmbeddedArticle)
    generic_reference = mongoengine.GenericReferenceField(choices=[Article, Editor])
    generic_embedded_document = mongoengine.GenericEmbeddedDocumentField(
        choices=[EmbeddedArticle, EmbeddedFoo]
    )
    generic_references = mongoengine.ListField(
        mongoengine.GenericReferenceField(choices=[Article, Editor])
    )


class Player(mongoengine.Document):

    meta = {"collection": "test_player"}
    first_name = mongoengine.StringField(required=True)
    last_name = mongoengine.StringField(required=True)
    opponent = mongoengine.ReferenceField("Player")
    players = mongoengine.ListField(mongoengine.ReferenceField("Player"))
    articles = mongoengine.ListField(mongoengine.ReferenceField("Article"))
    embedded_list_articles = mongoengine.EmbeddedDocumentListField(EmbeddedArticle)


class Parent(mongoengine.Document):

    meta = {"collection": "test_parent", "allow_inheritance": True}
    bar = mongoengine.StringField()
    loc = mongoengine.MultiPolygonField()


class CellTower(mongoengine.Document):

    meta = {"collection": "test_cell_tower"}
    code = mongoengine.StringField()
    base = mongoengine.PolygonField()
    coverage_area = mongoengine.MultiPolygonField()


class Child(Parent):

    meta = {"collection": "test_child"}
    baz = mongoengine.StringField()
    loc = mongoengine.PointField()


class ProfessorMetadata(mongoengine.EmbeddedDocument):

    meta = {"collection": "test_professor_metadata"}
    id = mongoengine.StringField(primary_key=False)
    first_name = mongoengine.StringField()
    last_name = mongoengine.StringField()
    departments = mongoengine.ListField(mongoengine.StringField())


class ProfessorVector(mongoengine.Document):

    meta = {"collection": "test_professor_vector"}
    vec = mongoengine.ListField(mongoengine.FloatField())
    metadata = mongoengine.EmbeddedDocumentField(ProfessorMetadata)


class ParentWithRelationship(mongoengine.Document):

    meta = {"collection": "test_parent_reference"}
    before_child = mongoengine.ListField(
        mongoengine.ReferenceField("ChildRegisteredBefore")
    )
    after_child = mongoengine.ListField(
        mongoengine.ReferenceField("ChildRegisteredAfter")
    )
    name = mongoengine.StringField()


class ChildRegisteredBefore(mongoengine.Document):

    meta = {"collection": "test_child_before_reference"}
    parent = mongoengine.ReferenceField(ParentWithRelationship)
    name = mongoengine.StringField()


class ChildRegisteredAfter(mongoengine.Document):

    meta = {"collection": "test_child_after_reference"}
    parent = mongoengine.ReferenceField(ParentWithRelationship)
    name = mongoengine.StringField()


class ErroneousModel(mongoengine.Document):
    meta = {"collection": "test_colliding_objects_model"}

    objects = mongoengine.ListField(mongoengine.StringField())


class Bar(mongoengine.EmbeddedDocument):
    some_list_field = mongoengine.ListField(mongoengine.StringField(), required=True)


class Foo(mongoengine.Document):
    bars = mongoengine.EmbeddedDocumentListField(Bar)
