from typing import Union

from starlette.responses import Response, JSONResponse, PlainTextResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from starlette_context import request_cycle_context
from starlette_context.middleware import RawContextMiddleware
from starlette_context.errors import ConfigurationError

from fastapi_context.config import ContextConfig
from fastapi_context.exceptions import ContextMiddlewareConfigError, ContextMiddlewareError


class FastAPiContextMiddleware(RawContextMiddleware):

    def __init__(self, app: ASGIApp, context_config: ContextConfig) -> None:  # type: ignore
        self.app = app
        self.context_config = context_config
        if not isinstance(self.context_config, ContextConfig):
            raise ContextMiddlewareConfigError(
                f"app.fastapi_context_config is not a valid instance"
            )
        self.plugins = self.context_config.plugins
        self.error_response = self.context_config.error_response

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            for plugin in self.plugins:
                await plugin.enrich_response(message)
            await send(message)

        request = self.get_request_object(scope, receive, send)

        try:
            context = await self.set_context(request)
        except ContextMiddlewareError as error:
            error_response = self.make_response(error=error)
            return await self.send_response(error_response, send)

        with request_cycle_context(context):
            await self.app(scope, receive, send_wrapper)

    def make_response(self, error: ContextMiddlewareError) -> Union[JSONResponse, Response, PlainTextResponse]:
        if issubclass(self.context_config.error_response, JSONResponse):
            json_data_class = self.context_config.json_data_class.create_model_by_error(error=error)
            return self.context_config.error_response(
                content=json_data_class.model_dump(by_alias=True), status_code=error.status_code
            )
        else:
            return self.context_config.error_response(content=error.message, status_code=error.status_code)
