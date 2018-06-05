import graphene
from functools import partial

from .utils import fields_to_args


def get_model_args(resolvable, only_fields, exclude_fields):
    def filter(kv):
        name = kv[0]
        is_in_only_in = not only_fields or name in only_fields
        is_excluded = name in exclude_fields
        return is_in_only_in and not is_excluded

    fields = resolvable._meta.fields
    args = fields_to_args(fields.items(), filter)
    return args


def generate_create_mutation(resolvable, only_fields=(), exclude_fields=()):

    def create_mutate(self, info, **kwargs):
        resolvable = kwargs.pop('resolvable')
        mutation = kwargs.pop('klass')
        instance = resolvable._meta.model(**kwargs)
        instance.save()
        data = {
            resolvable._meta.model.__name__.lower(): instance,
            'success': True
        }
        return mutation(**data)

    model = resolvable._meta.model
    CreateMutation = type(
        "Create{}".format(model.__name__),
        (graphene.Mutation,),
        {
            "mutate": partial(create_mutate, resolvable=resolvable, klass=lambda **kwargs: CreateMutation(**kwargs)),
            "success": graphene.Boolean(required=True),
            "{}".format(model.__name__.lower()): graphene.Field(resolvable),
            "Arguments": type(
                "Arguments",
                (),
                dict(get_model_args(resolvable, only_fields, exclude_fields))
            )
        }
    )

    return CreateMutation
