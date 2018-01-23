# from __future__ import absolute_import
# from graphene.core.fields import Field
# from graphene.core.types.base import FieldType
# from graphene.core.types.definitions import List
# 
# from .exceptions import SkipField
# from .utils import get_type_for_document
# 
# 
# class MongoEngineDocumentField(FieldType):
#     def __init__(self, document, *args, **kwargs):
#         self.document = document
#         super(MongoEngineDocumentField, self).__init__(*args, **kwargs)
# 
#     def internal_type(self, schema):
#         _type = self.get_object_type(schema)
#         if not _type and self.parent._meta.only_fields:
#             raise Exception(
#                     "Collection %r is not accessible by the schema. "
#                     "You can either register the type manually "
#                     "using @schema.register. "
#                     "Or disable the field in %s" % (
#                         self.document,
#                         self.parent,
#                     )
#             )
#         if not _type:
#             raise SkipField()
#         return schema.T(_type)
# 
#     def get_object_type(self, schema):
#         return get_type_for_document(schema, self.document)
# 
#     @property
#     def List(self):
#         return List(self, *self.args, **self.kwargs)
# 
