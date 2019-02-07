import json

import graphene

from .setup import fixtures
from .models import (
    Child, Editor, Player, Reporter, ProfessorVector, Parent, CellTower
)
from .types import (
    ChildType, EditorType, PlayerType, ReporterType, ProfessorVectorType, ParentType, CellTowerType
)


def test_should_query_editor(fixtures):

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
                firstName,
                metadata,
                company {
                    name
                }
            }
            editors {
                firstName,
                lastName
            }
        }
    '''
    expected = {
        'editor': {
            'firstName': 'Penny',
            'company': {"name": "Newsco"}
        },
        'editors': [{
            'firstName': 'Penny',
            'lastName': 'Hardaway'
        }, {
            'firstName': 'Grant',
            'lastName': 'Hill'
        }, {
            'firstName': 'Dennis',
            'lastName': 'Rodman'
        }]
    }
    expected_metadata = '{"age": "20", "nickname": "$1"}'

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    metadata = result.data['editor'].pop('metadata')
    assert (json.loads(metadata)) == dict(json.loads(expected_metadata))
    assert json.dumps(result.data, sort_keys=True) == \
        json.dumps(expected, sort_keys=True)


def test_should_query_reporter(fixtures):

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)

        def resolve_reporter(self, *args, **kwargs):
            return Reporter.objects.first()

    query = '''
        query ReporterQuery {
            reporter {
                firstName,
                lastName,
                email,
                articles {
                    headline
                },
                embeddedArticles {
                    headline
                },
                embeddedListArticles {
                    headline
                },
                awards
            }
        }
    '''
    expected = {
        'reporter': {
            'firstName': 'Allen',
            'lastName': 'Iverson',
            'email': 'ai@gmail.com',
            'articles': [
                {'headline': 'Hello'},
                {'headline': 'World'}
            ],
            'embeddedArticles': [
                {
                    'headline': 'Real'
                },
                {
                    'headline': 'World'
                }
            ],
            'embeddedListArticles': [
                {
                    'headline': 'World'
                },
                {
                    'headline': 'Real'
                }
            ],
            'awards': ['2010-mvp']
        }
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert dict(result.data['reporter']) == expected['reporter']


def test_should_custom_kwargs(fixtures):

    class Query(graphene.ObjectType):

        editors = graphene.List(EditorType, first=graphene.Int())

        def resolve_editors(self, *args, **kwargs):
            editors = Editor.objects()
            if 'first' in kwargs:
                editors = editors[:kwargs['first']]
            return list(editors)

    query = '''
        query EditorQuery {
            editors(first: 2) {
                firstName,
                lastName
            }
        }
    '''
    expected = {
        'editors': [
            {
                'firstName': 'Penny',
                'lastName': 'Hardaway'
            },
            {
                'firstName': 'Grant',
                'lastName': 'Hill'
            }
        ]
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert all(item in result.data['editors'] for item in expected['editors'])


def test_should_self_reference(fixtures):

    class Query(graphene.ObjectType):

        all_players = graphene.List(PlayerType)

        def resolve_all_players(self, *args, **kwargs):
            return Player.objects.all()

    query = '''
        query PlayersQuery {
            allPlayers {
                firstName,
                opponent {
                    firstName
                },
                players {
                    firstName
                }
            }
        }
    '''
    expected = {
        'allPlayers': [
            {
                'firstName': 'Michael',
                'opponent': None,
                'players': [
                    {
                        'firstName': 'Magic'
                    }
                ]
            },
            {
                'firstName': 'Magic',
                'opponent': {
                    'firstName': 'Michael'
                },
                'players': [
                    {
                        'firstName': 'Michael'
                    }
                ]
            },
            {
                'firstName': 'Larry',
                'opponent': None,
                'players': [
                    {
                        'firstName': 'Michael'
                    },
                    {
                        'firstName': 'Magic'
                    }
                ]
            },
            {
                 'firstName': 'Chris',
                 'opponent': None,
                 'players': []
            }
        ]
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == \
        json.dumps(expected, sort_keys=True)


def test_should_query_with_embedded_document(fixtures):

    class Query(graphene.ObjectType):
        professor_vector = graphene.Field(ProfessorVectorType, id=graphene.String())

        def resolve_professor_vector(self, info, id):
            return ProfessorVector.objects(metadata__id=id).first()

    query = """
        query {
          professorVector(id: "5e06aa20-6805-4eef-a144-5615dedbe32b") {
            vec
            metadata {
                firstName
            }
          }
        }
    """

    expected = {
        'professorVector': {
            'vec': [1.0, 2.3],
            'metadata': {
                'firstName': 'Steven'
            }
        }
    }
    schema = graphene.Schema(query=Query, types=[ProfessorVectorType])
    result = schema.execute(query)
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == \
        json.dumps(expected, sort_keys=True)


def test_should_query_child(fixtures):

    class Query(graphene.ObjectType):

        children = graphene.List(ChildType)

        def resolve_children(self, *args, **kwargs):
            return list(Child.objects.all())

    query = '''
        query Query {
            children {
                bar,
                baz,
                loc {
                     type,
                     coordinates
                }
            }
        }
    '''
    expected = {
        'children': [
            {
                'bar': 'BAR',
                'baz': 'BAZ',
                'loc': None
            }, {
                'bar': 'bar',
                'baz': 'baz',
                'loc': {
                    'type': 'Point',
                    'coordinates': [10.0, 20.0]
                }
            }
        ]
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == \
        json.dumps(expected, sort_keys=True)


def test_should_query_cell_tower(fixtures):

    class Query(graphene.ObjectType):

        cell_towers = graphene.List(CellTowerType)

        def resolve_cell_towers(self, *args, **kwargs):
            return list(CellTower.objects.all())

    query = '''
        query Query {
            cellTowers {
                code,
                coverageArea {
                     type,
                     coordinates
                }
            }
        }
    '''
    expected = {
        'cellTowers': [
            {
                'code': 'bar',
                'coverageArea': {
                    'type': 'MultiPolygon',
                    'coordinates': [[[
                        [-43.36556, -22.99669],
                        [-43.36539, -23.01928],
                        [-43.26583, -23.01802],
                        [-43.36717, -22.98855],
                        [-43.36636, -22.99351],
                        [-43.36556, -22.99669]]]]
                }
            }
        ]
    }

    schema = graphene.Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert json.dumps(result.data, sort_keys=True) == \
        json.dumps(expected, sort_keys=True)
