"""Basic message admin routes."""

from aiohttp import web
from aiohttp_apispec import docs, match_info_schema, request_schema

from marshmallow import fields, Schema

from aries_cloudagent.connections.models.connection_record import ConnectionRecord
from aries_cloudagent.messaging.valid import UUIDFour
from aries_cloudagent.storage.error import StorageNotFoundError

from .messages.basicmessage import BasicMessage


class SendMessageSchema(Schema):
    """Request schema for sending a message."""

    content = fields.Str(description="Message content", example="Hello")


class ConnIdMatchInfoSchema(Schema):
    """Path parameters and validators for request taking connection id."""

    conn_id = fields.Str(
        description="Connection identifier", required=True, example=UUIDFour.EXAMPLE
    )


@docs(tags=["basicmessage"], summary="Send a basic message to a connection")
@match_info_schema(ConnIdMatchInfoSchema())
@request_schema(SendMessageSchema())
async def connections_send_message(request: web.BaseRequest):
    """
    Request handler for sending a basic message to a connection.

    Args:
        request: aiohttp request object

    """
    context = request.app["request_context"]
    connection_id = request.match_info["conn_id"]
    outbound_handler = request.app["outbound_message_router"]
    params = await request.json()

    try:
        connection = await ConnectionRecord.retrieve_by_id(context, connection_id)
    except StorageNotFoundError:
        raise web.HTTPNotFound()

    if connection.is_ready:
        msg = BasicMessage(content=params["content"])
        await outbound_handler(msg, connection_id=connection_id)

    return web.json_response({})


async def register(app: web.Application):
    """Register routes."""

    app.add_routes(
        [web.post("/connections/{conn_id}/send-message", connections_send_message)]
    )
