import pytest
from .models import (
    Article, Editor, EmbeddedArticle, Player,
    Reporter, Child, ProfessorMetadata, ProfessorVector,
)


@pytest.fixture(scope='module')
def fixtures():
    Editor.drop_collection()
    editor1 = Editor(
        id='1',
        first_name='Penny',
        last_name='Hardaway',
        metadata={'age': '20', 'nickname': '$1'}
    )
    editor1.save()
    editor2 = Editor(
        id='2',
        first_name='Grant',
        last_name='Hill'
    )
    editor2.save()
    editor3 = Editor(
        id='3',
        first_name='Dennis',
        last_name='Rodman'
    )
    editor3.save()

    Article.drop_collection()
    article1 = Article(headline='Hello', editor=editor1)
    article1.save()
    article2 = Article(headline='World', editor=editor2)
    article2.save()

    Reporter.drop_collection()
    reporter1 = Reporter(
        id='1',
        first_name='Allen',
        last_name='Iverson',
        email='ai@gmail.com',
        awards=['2010-mvp']
    )
    reporter1.articles = [article1, article2]
    embedded_article1 = EmbeddedArticle(
        headline='Real',
        editor=editor1
    )
    embedded_article2 = EmbeddedArticle(
        headline='World',
        editor=editor2
    )
    reporter1.embedded_articles = [embedded_article1, embedded_article2]
    reporter1.embedded_list_articles = [embedded_article2, embedded_article1]
    reporter1.save()

    Player.drop_collection()
    player1 = Player(
        first_name='Michael',
        last_name='Jordan'
    )
    player1.save()
    player2 = Player(
        first_name='Magic',
        last_name='Johnson',
        opponent=player1
    )
    player2.save()
    player3 = Player(
        first_name='Larry',
        last_name='Bird',
        players=[player1, player2]
    )
    player3.save()

    player1.players = [player2]
    player1.save()

    player2.players = [player1]
    player2.save()

    Child.drop_collection()
    child1 = Child(bar='BAR', baz='BAZ')
    child1.save()

    child2 = Child(bar='bar', baz='baz')
    child2.save()

    ProfessorVector.drop_collection()
    professor_metadata = ProfessorMetadata(
        id='5e06aa20-6805-4eef-a144-5615dedbe32b',
        first_name='Steven',
        last_name='Curry',
        departments=['NBA', 'MLB']
    )
    professor_vector = ProfessorVector(
        vec=[1.0, 2.3],
        metadata=professor_metadata
    )
    professor_vector.save()
