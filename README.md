# Auth check and more plugins for fastApi

## Getting Started

provide SDK in the following programming languages:

- Python

### Python

1. Install the `fastApi-context` package:

    ```bash
    pip install fastApi-context
    ```

2. Initialize your fastapi client

    ```py
    from fastapi import FastAPI

    app = FastAPI()

    ```


3. Configure plugins
      
   1) JwtAuthPlugin
   + for JWT authentication you can use the `JwtAuthPlugin` plugin. This plugin allows you to configure JWT authentication for your FastAPI application.
       ```py
      from fastapi_context.config import JWTAuthPluginConfig
      from fastapi_context.plugins.auth_plugin import JwtAuthPlugin
      
      jwt_auth_plugin = JwtAuthPlugin(
               auth_plugin_config=JWTAuthPluginConfig(
               key="jwt payload key in context",
               url_white_list=["url white list"],
               user_class=None,  # user class for decode jwt payload
               get_token="token",  # get jwt token way, value is string or callable
               jwt_secret="Your App Jwt secret",
               jwt_algorithms=["HS256"],  # Your App Jwt algorithms
           )
       )
       ```

   2) RedisAuthPlugin
   + for Redis authentication you can use the `RedisAuthPlugin` plugin. This plugin allows you to configure Redis authentication for your FastAPI application.
       ```py
      from fastapi_context.config import RedisConfig, RedisAuthPluginConfig
      from fastapi_context.plugins.auth_plugin import RedisAuthPlugin
      
       redis_auth_plugin = RedisAuthPlugin(
                auth_plugin_config=RedisAuthPluginConfig(
                key="redis payload key in context",
                url_white_list=["url white list"],
                user_class=None,  # user class for decode jwt payload
                get_token="token",  # get jwt token way, value is string or callable
                redis_token_key_prefix="your redis token key prefix",
                # config redis client
                # redis_client_function or redis_config must be provided. At least one of these two parameters needs to be set in order for the configuration to work correctly.   
                redis_config=RedisConfig(
                    host=settings.Redis.HOST,
                    port=settings.Redis.PORT,
                    db=settings.Redis.TOKEN_DB_NUM,
                    password=settings.Redis.PASSWORD,
                    decode_responses=True,
                ),
               # sync or async both support, see redis.Redis or redis.asyncio.client.Redis, Prioritize async selection
               # redis_client_function=function,
             )
       )
       ```

4. Register middleware

    ```py
    from fastapi_context.config import ContextConfig, JsonResponseConfig
    from fastapi_context.exceptions import ContextMiddlewareError
    from fastapi_context.context_middleware import FastAPiContextMiddleware
    from starlette.responses import JSONResponse
    from pydantic import BaseModel, Field
    
    # when you set `JSONResponse` for error_response, you need to define a custom response model or use default model `JsonResponseConfig`.
    #  You can define your own BaseModel and implement a custom return type by overriding the create_model_by_error method.
   class MyJsonResponseConfig(BaseModel):
       status: int = Field(default=0, title="status")
       data: Any = Field(default=None, title="data")
       msg: str = Field(default="", title="message")
      
       @classmethod
       def create_model_by_error(cls, error: ContextMiddlewareError):
           """
           create json data by context error
           """
           return cls(status=error.error_code, data=error.data, msg=error.message)

   app.add_middleware(
        FastAPiContextMiddleware,
            context_config=ContextConfig(
                plugins=[
                    jwt_auth_plugin,
                    # redis_auth_plugin,
                ],
                error_response=JSONResponse,
                json_data_class=MyJsonResponseConfig,
      
            ),
    )
    ```