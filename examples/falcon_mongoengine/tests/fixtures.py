import pytest
from examples.falcon_mongoengine.models import Category, Bookmark


def fixture_category_data():
    Category.drop_collection()
    category_one = Category(name="Travel", color="#ed008c")
    category_one.save()

    category_two = Category(name="Work", color="#1769ff")
    category_two.save()

    return category_one, category_two


@pytest.fixture(scope="module")
def fixtures_data():
    category_one, category_two = fixture_category_data()

    Bookmark.drop_collection()
    bookmark_one = Bookmark(
        name="Travel tips",
        url="https://www.traveltips.test",
        category=category_one,
        tags=["travel", "tips", "howto"],
    )
    bookmark_one.save()

    bookmark_two = Bookmark(
        name="DIY vacation",
        url="https://www.diyvacation.test",
        category=category_one,
        tags=["travel", "diy", "holiday", "vacation"],
    )
    bookmark_two.save()

    bookmark_three = Bookmark(
        name="Awesome python",
        url="https://awesomelists.top/#repos/vinta/awesome-python",
        category=category_two,
        tags=["python", "dev", "awesome", "tutorial"],
    )
    bookmark_three.save()

    return True
