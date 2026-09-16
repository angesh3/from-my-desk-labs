"""From My Desk website and interactive lab portal."""

from __future__ import annotations

import mimetypes
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Mount

from from_my_desk.catalog import CatalogError, LabEntry, latest_lab, load_catalog, sort_labs_by_edition
from from_my_desk.config import (
    APP_VERSION,
    ResourceConfigError,
    get_settings,
    validate_runtime_resources,
)
from from_my_desk.telemetry import public_telemetry_config, security_headers_for_request
from know_your_agent.gateway import get_bundle, router as lab_router
from know_your_agent.loader import PolicyConfigError
from know_your_agent.rate_limit import SlidingWindowLimiter
from delegated_authority.gateway import get_lab002_bundle, router as lab002_router
from delegated_authority.loader import Lab002ConfigError
from agent_access_control.gateway import get_lab003_bundle, router as lab003_router
from agent_access_control.loader import Lab003ConfigError
from agent_escalation_boundary.gateway import get_lab004_bundle, router as lab004_router
from agent_escalation_boundary.loader import Lab004ConfigError
from verifiable_action_receipts.gateway import get_lab005_bundle, router as lab005_router
from verifiable_action_receipts.loader import Lab005ConfigError

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")

_settings = get_settings()
TEMPLATES = Jinja2Templates(directory=str(_settings.website_template_dir))

def _security_headers(request: Request) -> Dict[str, str]:
    settings = get_settings()
    return security_headers_for_request(settings, request.url.hostname or "")

_limiter: Optional[SlidingWindowLimiter] = None
_catalog: Optional[List[LabEntry]] = None


def get_catalog() -> List[LabEntry]:
    global _catalog
    if _catalog is None:
        _catalog = load_catalog(get_settings().catalog_path)
    return _catalog


def reset_catalog() -> None:
    global _catalog
    _catalog = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _limiter
    settings = get_settings()
    try:
        validate_runtime_resources(settings)
        get_catalog()
        os.environ.setdefault("POLICY_DIR", str(settings.policy_dir))
        get_bundle()
        os.environ.setdefault("LAB002_DATA_DIR", str(settings.lab002_data_dir))
        os.environ.setdefault("LAB002_POLICY_DIR", str(settings.lab002_policy_dir))
        get_lab002_bundle()
        os.environ.setdefault("LAB003_DATA_DIR", str(settings.lab003_data_dir))
        os.environ.setdefault("LAB003_POLICY_DIR", str(settings.lab003_policy_dir))
        get_lab003_bundle()
        os.environ.setdefault("LAB004_DATA_DIR", str(settings.lab004_data_dir))
        os.environ.setdefault("LAB004_POLICY_DIR", str(settings.lab004_policy_dir))
        get_lab004_bundle()
        os.environ.setdefault("LAB005_DATA_DIR", str(settings.lab005_data_dir))
        os.environ.setdefault("LAB005_POLICY_DIR", str(settings.lab005_policy_dir))
        get_lab005_bundle()
    except (
        CatalogError,
        PolicyConfigError,
        Lab002ConfigError,
        Lab003ConfigError,
        Lab004ConfigError,
        Lab005ConfigError,
        ResourceConfigError,
    ) as exc:
        raise RuntimeError(
            "Refusing to start with unsafe catalog, policy, or missing website resources."
        ) from exc
    _limiter = SlidingWindowLimiter(settings.rate_limit_per_minute)
    yield


app = FastAPI(
    title="From My Desk",
    description=(
        "From My Desk — ideas at the intersection of AI, engineering, architecture, "
        "security, and leadership, with occasional interactive labs."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {
            "/evaluate",
            "/api/evaluate",
            "/api/labs/002/evaluate",
            "/api/labs/003/evaluate",
            "/api/labs/004/evaluate",
            "/api/labs/005/generate",
        } and request.method == "POST":
            limiter = _limiter
            if limiter is not None:
                client = request.client.host if request.client else "unknown"
                if not limiter.allow(client):
                    return JSONResponse(
                        status_code=429,
                        content={
                            "decision": "deny",
                            "reason_code": "invalid_request",
                            "reason": "Too many evaluation requests. Try again shortly.",
                            "detail": "rate_limited",
                        },
                        headers=_security_headers(request),
                    )
            content_length = request.headers.get("content-length")
            if content_length and content_length.isdigit() and int(content_length) > 16_384:
                return JSONResponse(
                    status_code=413,
                    content={
                        "reason_code": "invalid_request",
                        "reason": "Request body is too large.",
                    },
                    headers=_security_headers(request),
                )
        response = await call_next(request)
        for key, value in _security_headers(request).items():
            response.headers.setdefault(key, value)
        return response


app.add_middleware(SecurityHeadersMiddleware)


def _page_context(request: Request, **extra: Any) -> Dict[str, Any]:
    settings = get_settings()
    host = request.url.hostname or ""
    labs = get_catalog()
    published_sorted = sort_labs_by_edition(
        [item for item in labs if item.status == "published"]
    )
    current_latest = latest_lab(labs)
    earlier_labs = [
        item for item in published_sorted if item.id != (current_latest.id if current_latest else None)
    ]
    return {
        "request": request,
        "github_url": settings.github_url,
        "newsletter_url": settings.newsletter_url,
        "labs": labs,
        "published_labs": published_sorted,
        "latest_lab": current_latest,
        "earlier_labs": earlier_labs,
        "featured": current_latest,
        "current_path": request.url.path,
        "footer_note": "From My Desk · Written and built by Angesh Vikram",
        "disclaimer": (
            "Educational simulation with fictional companies, agents, accounts, "
            "tickers, and thresholds. Not investment advice. No order is executed."
        ),
        "telemetry": public_telemetry_config(settings, host),
        **extra,
    }


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    response = await request_validation_exception_handler(request, exc)
    if request.url.path in {
        "/evaluate",
        "/api/evaluate",
        "/api/labs/002/evaluate",
        "/api/labs/003/evaluate",
        "/api/labs/004/evaluate",
        "/api/labs/005/generate",
    }:
        return JSONResponse(
            status_code=422,
            content={
                "reason_code": "invalid_request",
                "reason": "The request could not be validated. Check types and required fields.",
                "execution": "not_performed",
            },
        )
    return response


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(
        status_code=500,
        content={
            "reason_code": "invalid_request",
            "reason": "The service could not complete this request.",
            "execution": "not_performed",
        },
    )


# API / health routes first so mounts cannot shadow them.
app.include_router(lab_router)
app.include_router(lab002_router)
app.include_router(lab003_router)
app.include_router(lab004_router)
app.include_router(lab005_router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "home.html", _page_context(request))


@app.get("/labs", response_class=HTMLResponse)
def labs_index(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "labs.html", _page_context(request))


def _lab_by_slug(slug: str) -> LabEntry:
    for item in get_catalog():
        if item.slug == slug:
            return item
    raise HTTPException(status_code=404, detail="Unknown lab.")


@app.get("/labs/{slug}", response_class=HTMLResponse)
def lab_page(request: Request, slug: str) -> HTMLResponse:
    entry = _lab_by_slug(slug)
    if slug == "know-your-agent":
        policy = get_bundle().policy
        return TEMPLATES.TemplateResponse(
            request,
            "lab.html",
            _page_context(
                request,
                lab=entry,
                policy_id=policy.policy_id,
                allow_max=str(policy.allow_max),
                confirm_max=str(policy.confirm_max),
                step_up_max=str(policy.step_up_max),
            ),
        )
    if slug == "delegated-authority":
        gif_path = get_settings().lab002_static_dir / "delegated-authority-trust-workflow.gif"
        return TEMPLATES.TemplateResponse(
            request,
            "lab002.html",
            _page_context(
                request,
                lab=entry,
                workflow_gif_available=gif_path.is_file(),
            ),
        )
    if slug == "agent-access-control":
        return TEMPLATES.TemplateResponse(
            request,
            "lab003.html",
            _page_context(request, lab=entry),
        )
    if slug == "agent-escalation-boundary":
        return TEMPLATES.TemplateResponse(
            request,
            "lab004.html",
            _page_context(request, lab=entry),
        )
    if slug == "verifiable-action-receipts":
        return TEMPLATES.TemplateResponse(
            request,
            "lab005.html",
            _page_context(request, lab=entry),
        )
    raise HTTPException(status_code=404, detail="This edition does not have an interactive page yet.")


# Static mounts last: specific lab assets, then global site assets.
app.mount(
    "/static/labs/001",
    StaticFiles(directory=str(_settings.lab_static_dir)),
    name="lab001-static",
)
app.mount(
    "/static/labs/002",
    StaticFiles(directory=str(_settings.lab002_static_dir)),
    name="lab002-static",
)
app.mount(
    "/static/labs/003",
    StaticFiles(directory=str(_settings.lab003_static_dir)),
    name="lab003-static",
)
app.mount(
    "/static/labs/004",
    StaticFiles(directory=str(_settings.lab004_static_dir)),
    name="lab004-static",
)
app.mount(
    "/static/labs/005",
    StaticFiles(directory=str(_settings.lab005_static_dir)),
    name="lab005-static",
)
app.mount(
    "/static",
    StaticFiles(directory=str(_settings.website_static_dir)),
    name="static",
)


def iter_route_table():
    """Yield route metadata in matching order for diagnostics and tests."""
    for route in app.routes:
        yield {
            "type": type(route).__name__,
            "path": getattr(route, "path", None),
            "name": getattr(route, "name", None),
            "methods": sorted(getattr(route, "methods", None) or []),
            "is_mount": isinstance(route, Mount),
        }
