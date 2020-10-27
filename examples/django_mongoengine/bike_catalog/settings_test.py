from .settings import *  # flake8: noqa

mongoengine.connect(
    "graphene-mongo-test", host="mongomock://localhost", alias="default"
)
