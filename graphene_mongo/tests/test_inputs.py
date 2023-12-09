import graphene
import pytest

from graphene.relay import Node

from .models import Article, Editor
from .nodes import ArticleNode, EditorNode
from .types import ArticleInput, EditorInput


@pytest.mark.asyncio
async def test_should_create(fixtures):
    class CreateArticle(graphene.Mutation):
        class Arguments:
            article = ArticleInput(required=True)

        article = graphene.Field(ArticleNode)

        async def mutate(self, info, article):
            article = Article(**article)
            article.save()

            return CreateArticle(article=article)

    class Query(graphene.ObjectType):
        node = Node.Field()

    class Mutation(graphene.ObjectType):
        create_article = CreateArticle.Field()

    query = """
        mutation ArticleCreator {
            createArticle(
                article: {headline: "My Article"}
            ) {
                article {
                    headline
                }
            }
        }
    """
    expected = {"createArticle": {"article": {"headline": "My Article"}}}
    schema = graphene.Schema(query=Query, mutation=Mutation)
    result = await schema.execute_async(query)
    assert not result.errors
    assert result.data == expected


@pytest.mark.asyncio
async def test_should_update(fixtures):
    class UpdateEditor(graphene.Mutation):
        class Arguments:
            id = graphene.ID(required=True)
            editor = EditorInput(required=True)

        editor = graphene.Field(EditorNode)

        async def mutate(self, info, id, editor):
            editor_to_update = Editor.objects.get(id=id)
            for key, value in editor.items():
                if value:
                    setattr(editor_to_update, key, value)
            editor_to_update.save()
            return UpdateEditor(editor=editor_to_update)

    class Query(graphene.ObjectType):
        node = Node.Field()

    class Mutation(graphene.ObjectType):
        update_editor = UpdateEditor.Field()

    query = """
        mutation EditorUpdater {
            updateEditor(
                id: "1"
                editor: {
                    lastName: "Lane"
                }
            ) {
                editor {
                    firstName
                    lastName
                }
            }
        }
    """
    expected = {"updateEditor": {"editor": {"firstName": "Penny", "lastName": "Lane"}}}
    schema = graphene.Schema(query=Query, mutation=Mutation)
    result = await schema.execute_async(query)
    # print(result.data)
    assert not result.errors
    assert result.data == expected
