import graphene
from functools import partial
from .types import MongoengineObjectType


def _create_input_factory(model, exclude_fields=('id', 'idempotency_key'), only_fields=()):
    return type(
        "Create{}Input".format(model.__name__),
        # (MongoengineInputObjectType,),
        (MongoengineObjectType,),
        {"Meta": type('Meta', (), dict(model=model, exclude_fields=exclude_fields, only_fields=only_fields))}
    )


def generate_create_mutation(resolvable, only_fields=(), exclude_fields=()):
    model = resolvable._meta.model
    # assert hasattr(model, "idempotency_key")

    # if not only_fields and not exclude_fields:
    #     only_fields = get_fields_from_resolvable(resolvable)

    def create_mutate(**kwargs):
        print("there" * 20)
        resolvable = kwargs.pop('resolvable')
        instance = kwargs.pop('klass')()
        model = resolvable._meta.model(**kwargs)
        model.save()
        instance.success = True
        return instance

    CreateInput = _create_input_factory(
        model, only_fields=only_fields, exclude_fields=exclude_fields)

    CreateMutation = type(
        "Create{}".format(model.__name__),
        (graphene.Mutation,),
        {
            "mutate": partial(create_mutate, resolvable=resolvable, klass=lambda: CreateMutation),
            "success": graphene.Boolean(required=True),
            "create_{}".format(model.__name__.lower()): graphene.Field(resolvable),
            "Arguments": type(
                "Arguments",
                (),
                dict(
                    idempotency_key=graphene.ID(),
                    input=CreateInput()
                ))
        }
    )

    # get_global_mutation_registry().register(CreateMutation, resolvable)
    return CreateMutation
