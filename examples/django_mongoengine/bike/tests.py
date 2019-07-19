from graphene.test import Client
from .schema import schema
from .fixtures import fixtures_data


def test_bikes_last_item_query(fixtures_data):
    query = '''
               {
               bikes(last: 1){
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
           }'''

    expected = {
        "data": {
            "bikes":
                {
                    "edges": [
                        {
                            "node": {
                                "name": "CAADX ULTEGRA",
                                "brand": "Cannondale",
                                "year": '2019',
                                "size": ['46', '51', '54', '58'],
                                "wheelSize": 28,
                                "type": "Gravel"
                            }
                        },
                    ]
                }
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected


def test_bikes_filter_by_type_item_query(fixtures_data):
    query = '''
               {
               bikes(first: 2, type: "MTB"){
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
           }'''

    expected = {
        "data": {
            "bikes":
                {
                    "edges": [
                        {
                            "node": {
                                "name": "Level R",
                                "brand": "Mondraker",
                                "year": '2020',
                                "size": ['S', 'M', 'L', 'XL'],
                                "wheelSize": 27.5,
                                "type": "MTB"
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
    query = '''{
               shopList{
                    name
                    address
                    website
                    }
            }'''

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
                }
            ]
        }
    }

    client = Client(schema)
    result = client.execute(query)
    assert result == expected
