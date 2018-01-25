import json

import graphene

from graphene.relay import Node

from .models import Editor, EmbeddedArticle, Reporter
from ..fields import MongoengineConnectionField
from ..types import MongoengineObjectType


def setup_fixtures():
    editor1 = Editor(first_name='Penny', last_name='Hardaway')
    editor1.save()
    editor2 = Editor(first_name='Grant', last_name='Hill')
    editor2.save()

    reporter = Reporter(first_name='Allen', last_name='Iverson',
                        email='ai@gmail.com', awards=['2010-mvp'])
    embedded_article1 = EmbeddedArticle(headline='Hello', editor=editor1)
    embedded_article2 = EmbeddedArticle(headline='World', editor=editor2)
    reporter.articles = [embedded_article1, embedded_article2]
    reporter.save()

setup_fixtures()


def test_should_query_editor_well():
    class EditorType(MongoengineObjectType):
        class Meta:
            model = Editor

    class Query(graphene.ObjectType):
       editor = graphene.Field(EditorType)
       editors = graphene.List(EditorType)

       def resolve_editor(self, *args, **kwargs):
           return Editor.objects.first()

       def resolve_editors(self, *args, **kwargs):
           return list(Editor.objects.all())

    query = '''
        query EditorQuery {
            editor {
                firstName
            }
            editors {
                firstName,
                lastName
            }
        }
    '''
    expected = {
        'editor': {
            'firstName': 'Penny'
        },
        'editors': [{
            'firstName': 'Penny',
            'lastName': 'Hardaway'
        }, {
            'firstName': 'Grant',
            'lastName': 'Hill'
        }]
        }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['editor']) == expected['editor']
    assert all(item in result.data['editors'] for item in expected['editors'])


def test_should_query_reporter_well():
    class EmbeddedArticleType(MongoengineObjectType):
        class Meta:
            model = EmbeddedArticle

    class ReporterType(MongoengineObjectType):
        class Meta:
            model = Reporter

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)

        def resolve_reporter(self, *args, **kwargs):
            Reporter.objects.first()

    query = '''
        query ReporterQuery {
            reporter {
                firstName,
                lastName,
                email,
                embeddedArticles,
                awards
            }
        }
    '''
    expected = {
        'reporter': {
            'firstName': 'Allen',
            'lastName': 'Iversion',
            'email': 'ai@gmail.com',
            'embeddedArticles': [
                
            ],
            'awards': ['2010-mvp']
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    print(result.data)

