import graphene

from graphene.relay import Node

from .models import (Article,)
from .types import (ArticleNode,)

def test_should_mutate_create():

    class CreateArticle(graphene.Mutation):

        class Arguments:

            headline = graphene.String()

        article = graphene.Field(ArticleNode)

        def mutate(self, info, headline):
            article = Article(
                headline=headline
            )
            article.save()

            return CreateArticle(article=article)

    class Query(graphene.ObjectType):

        node = Node.Field()

    class Mutation(graphene.ObjectType):

        create_article = CreateArticle.Field()

    query = '''
        mutation ArticleCreator {
            createArticle(
                headline: "My Article"
            ) {
                article {
                    headline
                }
            }
        }
    '''
    expected = {
        'createArticle': {
            'article': {
                'headline': 'My Article'
            }
        }
    }
    schema = graphene.Schema(query=Query, mutation=Mutation)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected

