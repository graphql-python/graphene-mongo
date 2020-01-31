import json
import falcon
from .schema import schema


def set_graphql_allow_header(
    req: falcon.Request, resp: falcon.Response, resource: object
):
    resp.set_header("Allow", "GET, POST, OPTIONS")


class HelloWorldResource:
    def on_get(self, req, resp):
        name = "Hello World!"
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({"respone": name, "status": resp.status})

    def on_post(self, req, resp):
        pass


@falcon.after(set_graphql_allow_header)
class GraphQLResource:
    def on_get(self, req, resp):
        query = req.params["query"]
        result = schema.execute(query)

        if result.data:
            data_ret = {"data": result.data}
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(data_ret, separators=(",", ":"))

    def on_post(self, req, resp):
        query = req.params["query"]
        result = schema.execute(query)
        if result.data:
            data_ret = {"data": result.data}
            resp.status = falcon.HTTP_200
            resp.body = json.dumps(data_ret, separators=(",", ":"))
