"""Server application."""
from ipaddress import IPv4Network, IPv6Network

from blacksheep import Application
from blacksheep.server.openapi.v3 import OpenAPIHandler
from blacksheep.server.remotes.forwarding import XForwardedHeadersMiddleware
from httpx import AsyncClient
from oes.interview_old.config.interview import (
    InterviewConfig,
    interviews_context,
    load_interview_config,
)
from oes.interview_old.server.settings import load_settings
from openapidocs.v3 import Info

app = Application()

docs = OpenAPIHandler(info=Info(title="OES Interview Service", version="0.1"))
docs.bind_app(app)

app.use_cors(
    allow_origins="*",
    allow_methods=("GET", "POST", "PUT", "DELETE"),
    allow_headers=(
        "Authorization",
        "Content-Type",
    ),
)


async def _set_base_path(request, handler):
    """Middleware to set root_path from uvicorn."""
    request.base_path = request.scope.get("root_path", "")
    return await handler(request)


@app.on_middlewares_configuration
def _configure_forwarded_headers(app: Application):
    app.middlewares.insert(0, _set_base_path)
    app.middlewares.insert(
        0,
        XForwardedHeadersMiddleware(
            # Allow X-Forwarded headers from private networks
            known_networks=[
                IPv4Network("127.0.0.0/8"),
                IPv4Network("10.0.0.0/8"),
                IPv4Network("172.16.0.0/12"),
                IPv4Network("192.168.0.0/16"),
                IPv6Network("fc00::/7"),
                IPv6Network("::1/128"),
            ]
        ),
    )


@app.on_start
async def on_start(app: Application):
    settings = load_settings()
    app.services.add_instance(settings)

    interviews = load_interview_config(settings.config_file)
    app.services.add_instance(interviews)

    app.services.add_instance(AsyncClient())


async def context_middleware(request, handler):
    interviews = app.service_provider[InterviewConfig]
    token = interviews_context.set(interviews)
    try:
        return await handler(request)
    finally:
        interviews_context.reset(token)


app.middlewares.append(context_middleware)
