import mongoengine
from graphene.test import Client
from examples.falcon_mongoengine.schema import schema
from .fixtures import fixtures_data

mongoengine.connect(
    "graphene-mongo-test", host="mongomock://localhost", alias="default"
)


def test_category_last_1_item_query(fixtures_data):
    query = """
               {
               categories(last: 1){
                   edges {
                   node {
                       name
                       color 
                       }
                   }
               }
           }"""

    expected = {
        "data": {
            "categories": {"edges": [{"node": {"name": "Work", "color": "#1769ff"}}]}
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected


def test_category_filter_item_query(fixtures_data):
    query = """
               {
               categories(name: "Work"){
                   edges {
                   node {
                       name
                       color 
                       }
                   }
               }
           }"""

    expected = {
        "data": {
            "categories": {"edges": [{"node": {"name": "Work", "color": "#1769ff"}}]}
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected


def test_bookmarks_first_2_items_query(fixtures_data):
    query = """
               {
               bookmarks(first: 2){
                   edges {
                   node {
                       name
                       url
                       category {
                            name
                            color
                            }
                       tags
                       }
                   }
               }
           }"""

    expected = {
        "data": {
            "bookmarks": {
                "edges": [
                    {
                        "node": {
                            "name": "Travel tips",
                            "url": "https://www.traveltips.test",
                            "category": {"name": "Travel", "color": "#ed008c"},
                            "tags": ["travel", "tips", "howto"],
                        }
                    },
                    {
                        "node": {
                            "name": "DIY vacation",
                            "url": "https://www.diyvacation.test",
                            "category": {"name": "Travel", "color": "#ed008c"},
                            "tags": ["travel", "diy", "holiday", "vacation"],
                        }
                    },
                ]
            }
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected


def test_bookmarks_filter_items_query(fixtures_data):
    query = """
               {
               bookmarks(first: 1, name: "Awesome python"){
                   edges {
                   node {
                       name
                       url
                       category {
                            name
                            color
                            }
                       tags
                       }
                   }
               }
           }"""

    expected = {
        "data": {
            "bookmarks": {
                "edges": [
                    {
                        "node": {
                            "name": "Awesome python",
                            "url": "https://awesomelists.top/#repos/vinta/awesome-python",
                            "category": {"name": "Work", "color": "#1769ff"},
                            "tags": ["python", "dev", "awesome", "tutorial"],
                        }
                    }
                ]
            }
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected
