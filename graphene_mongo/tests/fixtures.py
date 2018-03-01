from .models import Article, Editor, EmbeddedArticle, Player, Reporter


def setup_fixtures():
    Editor.drop_collection()
    editor1 = Editor(first_name='Penny', last_name='Hardaway')
    editor1.save()
    editor2 = Editor(first_name='Grant', last_name='Hill')
    editor2.save()
    editor3 = Editor(first_name='Dennis', last_name='Rodman')
    editor3.save()

    Article.drop_collection()
    article1 = Article(headline='Hello', editor=editor1)
    article1.save()
    article2 = Article(headline='World', editor=editor2)
    article2.save()

    Reporter.drop_collection()
    reporter = Reporter(first_name='Allen', last_name='Iverson',
                        email='ai@gmail.com',  awards=['2010-mvp'])
    reporter.articles = [article1, article2]
    embedded_article1 = EmbeddedArticle(
        headline='Real',
        editor=editor1
    )
    embedded_article2 = EmbeddedArticle(
        headline='World',
        editor=editor2
    )
    reporter.embedded_articles = [embedded_article1, embedded_article2]
    reporter.save()

    Player.drop_collection()
    player1 = Player(first_name='Michael', last_name='Jordan')
    player1.save()
    player2 = Player(first_name='Magic', last_name='Johnson', opponent=player1)
    player2.save()
    player3 = Player(first_name='Larry', last_name='Bird', players=[player1, player2])
    player3.save()

    player1.players = [player2]
    player1.save()

    player2.players = [player1]
    player2.save()
