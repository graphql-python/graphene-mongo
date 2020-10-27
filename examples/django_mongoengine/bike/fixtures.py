import pytest
from .models import Bike, Shop


def fixture_bike_data():
    Bike.drop_collection()
    bike_one = Bike(
        name="Level R",
        brand="Mondraker",
        year="2020",
        size=["S", "M", "L", "XL"],
        wheel_size=27.5,
        type="MTB",
    )
    bike_one.save()

    bike_two = Bike(
        name="CAADX ULTEGRA",
        brand="Cannondale",
        year="2019",
        size=["46", "51", "54", "58"],
        wheel_size=28,
        type="Gravel",
    )
    bike_two.save()

    bike_three = Bike(
        id="507f1f77bcf86cd799439011",
        name="Moterra Neo",
        brand="Cannondale",
        year="2019",
        size=["M", "L", "XL"],
        wheel_size=29,
        type="EBike",
    )
    bike_three.save()


def fixture_shop_data():
    Shop.drop_collection()
    shop_one = Shop(
        name="Big Wheel Bicycles",
        address="2438 Hart Ridge Road",
        website="https://www.bigwheelbike.test",
    )
    shop_one.save()
    shop_two = Shop(
        name="Bike Tech",
        address="2175 Pearl Street",
        website="https://www.biketech.test",
    )
    shop_two.save()


@pytest.fixture(scope="module")
def fixtures_data():
    fixture_bike_data()
    fixture_shop_data()

    return True
