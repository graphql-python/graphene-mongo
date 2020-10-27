import pytest
from django.urls import reverse
from django.test import RequestFactory
from graphene.test import Client
from .schema import schema
from .fixtures import fixtures_data


def test_bikes_first_item_query(fixtures_data):
    query = """
               {
               bikes(first: 1){
                   edges {
                   node {
                       name
                       brand
                       year
                       size
                       wheelSize
                       type
                       }
                   }
               }
           }"""

    expected = {
        "data": {
            "bikes": {
                "edges": [
                    {
                        "node": {
                            "name": "Level R",
                            "brand": "Mondraker",
                            "year": "2020",
                            "size": ["S", "M", "L", "XL"],
                            "wheelSize": 27.5,
                            "type": "MTB",
                        }
                    }
                ]
            }
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected


def test_bikes_filter_by_type_item_query(fixtures_data):
    query = """
               {
               bikes(first: 2, type: "Gravel"){
                   edges {
                   node {
                       name
                       brand
                       year
                       size
                       wheelSize
                       type
                       }
                   }
               }
           }"""

    expected = {
        "data": {
            "bikes": {
                "edges": [
                    {
                        "node": {
                            "name": "CAADX ULTEGRA",
                            "brand": "Cannondale",
                            "year": "2019",
                            "size": ["46", "51", "54", "58"],
                            "wheelSize": 28,
                            "type": "Gravel",
                        }
                    }
                ]
            }
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected


def test_shop_data_query(fixtures_data):
    query = """{
               shopList{
                    name
                    address
                    website
                    }
            }"""

    expected = {
        "data": {
            "shopList": [
                {
                    "name": "Big Wheel Bicycles",
                    "address": "2438 Hart Ridge Road",
                    "website": "https://www.bigwheelbike.test",
                },
                {
                    "name": "Bike Tech",
                    "address": "2175 Pearl Street",
                    "website": "https://www.biketech.test",
                },
            ]
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected


@pytest.mark.django_db
def test_create_bike_mutation():
    query = """
                    mutation {
                        createBike(bikeData:{
                                name:"Bullhorn",
                                brand:"Pegas",
                                year: "2019",
                                size: ["56", "58" ],
                                wheelSize: 28,
                                type: "Fixie"
                                }) {
                            bike {
                                name
                                brand
                                year
                                size
                                wheelSize
                                type
                            }
                        }
                    }
                  """

    expected = {
        "data": {
            "createBike": {
                "bike": {
                    "name": "Bullhorn",
                    "brand": "Pegas",
                    "year": "2019",
                    "size": ["56", "58"],
                    "wheelSize": 28,
                    "type": "Fixie",
                }
            }
        }
    }

    factory = RequestFactory()
    request = factory.post(reverse("graphql-query"))
    client = Client(schema)
    result = client.execute(query, context=request)
    assert result == expected


@pytest.mark.django_db
def test_update_bike_mutation():
    query = """
                    mutation {
                        updateBike(bikeData:{
                                id: "507f1f77bcf86cd799439011",
                                name:"Moterra Neo Updated",
                                year: "2020",
                                wheelSize: 27.5,
                                type: "EBike Updated"
                                }) {
                            bike {
                                name
                                brand
                                year
                                size
                                wheelSize
                                type
                            }
                        }
                    }
                  """

    expected = {
        "data": {
            "updateBike": {
                "bike": {
                    "name": "Moterra Neo Updated",
                    "brand": "Cannondale",
                    "year": "2020",
                    "size": ["M", "L", "XL"],
                    "wheelSize": 27.5,
                    "type": "EBike Updated",
                }
            }
        }
    }

    factory = RequestFactory()
    request = factory.post(reverse("graphql-query"))
    client = Client(schema)
    result = client.execute(query, context=request)
    print(result)
    assert result == expected


@pytest.mark.django_db
def test_delete_bike_mutation():
    query = """
                mutation {
                    deleteBike(id: "507f1f77bcf86cd799439011") {
                           success
                    }
                }
              """

    expected = {"data": {"deleteBike": {"success": True}}}

    factory = RequestFactory()
    request = factory.post(reverse("graphql-query"))
    client = Client(schema)
    result = client.execute(query, context=request)
    assert result == expected
