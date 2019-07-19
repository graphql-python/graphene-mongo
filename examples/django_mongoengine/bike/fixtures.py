import pytest
from .models import Bike


@pytest.fixture(scope='module')
def fixtures_data():
    Bike.drop_collection()
    bike_one = Bike(
        name='Level R',
        brand='Mondraker',
        year='2020',
        size=['S', 'M', 'L', 'XL'],
        wheel_size=27.5,
        type='MTB'
    )
    bike_one.save()

    bike_two = Bike(
        name='CAADX ULTEGRA',
        brand='Cannondale',
        year='2019',
        size=['46', '51', '54', '58'],
        wheel_size=28,
        type='Gravel'
    )
    bike_two.save()

    return True
