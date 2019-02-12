import pytest

from datetime import datetime
from .models import (
    Article, Editor, EmbeddedArticle, Player,
    Reporter, Child, ProfessorMetadata, ProfessorVector,
    ChildRegisteredBefore, ChildRegisteredAfter,
    ParentWithRelationship, CellTower,
    Publisher)


@pytest.fixture(scope='module')
def fixtures():
    Publisher.drop_collection()
    publisher1 = Publisher(name="Newsco")
    publisher1.save()

    Editor.drop_collection()
    editor1 = Editor(
        id='1',
        first_name='Penny',
        last_name='Hardaway',
        metadata={'age': '20', 'nickname': '$1'},
        company=publisher1
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
    pub_date = datetime.strptime('2020-01-01', '%Y-%m-%d')
    article1 = Article(headline='Hello', editor=editor1, pub_date=pub_date)
    article1.save()
    article2 = Article(headline='World', editor=editor2, pub_date=pub_date)
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

    player4 = Player(
        first_name='Chris',
        last_name='Webber'
    )
    player4.save()

    Child.drop_collection()
    child1 = Child(bar='BAR', baz='BAZ')
    child1.save()

    child2 = Child(bar='bar', baz='baz', loc=[10, 20])
    child2.save()

    CellTower.drop_collection()
    ct = CellTower(code='bar', coverage_area=[[[
                        [-43.36556, -22.99669],
                        [-43.36539, -23.01928],
                        [-43.26583, -23.01802],
                        [-43.36717, -22.98855],
                        [-43.36636, -22.99351],
                        [-43.36556, -22.99669]]]])
    ct.save()
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

    ParentWithRelationship.drop_collection()
    ChildRegisteredAfter.drop_collection()
    ChildRegisteredBefore.drop_collection()

    # This is one messed up family

    # She'd better have presence this time
    child3 = ChildRegisteredBefore(name="Akari")
    child4 = ChildRegisteredAfter(name="Kyouko")
    child3.save()
    child4.save()

    parent = ParentWithRelationship(
        name="Yui",
        before_child=[child3],
        after_child=[child4]
    )

    parent.save()

    child3.parent = child4.parent = parent
    child3.save()
    child4.save()
    return True