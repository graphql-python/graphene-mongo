import graphene
from django.core.exceptions import ObjectDoesNotExist
from .models import Bike
from .types import BikeType


class BikeInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()
    brand = graphene.String()
    year = graphene.String()
    size = graphene.List(graphene.String)
    wheel_size = graphene.Float()
    type = graphene.String()


class CreateBikeMutation(graphene.Mutation):
    bike = graphene.Field(BikeType)

    class Arguments:
        bike_data = BikeInput(required=True)

    def mutate(self, info, bike_data=None):
        bike = Bike(
            name=bike_data.name,
            brand=bike_data.brand,
            year=bike_data.year,
            size=bike_data.size,
            wheel_size=bike_data.wheel_size,
            type=bike_data.type,
        )
        bike.save()

        return CreateBikeMutation(bike=bike)


class UpdateBikeMutation(graphene.Mutation):
    bike = graphene.Field(BikeType)

    class Arguments:
        bike_data = BikeInput(required=True)

    @staticmethod
    def get_object(id):
        return Bike.objects.get(pk=id)

    def mutate(self, info, bike_data=None):
        bike = UpdateBikeMutation.get_object(bike_data.id)
        if bike_data.name:
            bike.name = bike_data.name
        if bike_data.brand:
            bike.brand = bike_data.brand
        if bike_data.year:
            bike.year = bike_data.year
        if bike_data.size:
            bike.size = bike_data.size
        if bike_data.wheel_size:
            bike.wheel_size = bike_data.wheel_size
        if bike_data.type:
            bike.type = bike_data.type

        bike.save()

        return UpdateBikeMutation(bike=bike)


class DeleteBikeMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        try:
            Bike.objects.get(pk=id).delete()
            success = True
        except ObjectDoesNotExist:
            success = False

        return DeleteBikeMutation(success=success)
