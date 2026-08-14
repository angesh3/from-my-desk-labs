"""From My Desk website and interactive lab portal."""

from __future__ import annotations

import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from from_my_desk.catalog import CatalogError, LabEntry, featured_lab, load_catalog
from from_my_desk.config import APP_VERSION, get_settings
from from_my_desk.telemetry import public_telemetry_config
from know_your_agent.gateway import get_bundle, router as lab_router
from know_your_agent.loader import PolicyConfigError
from know_your_agent.rate_limit import SlidingWindowLimiter

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")

WEBSITE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(WEBSITE_DIR / "templates"))
LAB_001_STATIC = Path(
    os.environ.get("LAB_STATIC_DIR") or str(get_settings().lab_static_dir)
)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
}

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
        get_catalog()
        os.environ.setdefault("POLICY_DIR", str(settings.policy_dir))
        get_bundle()
    except (CatalogError, PolicyConfigError) as exc:
        raise RuntimeError("Refusing to start with unsafe catalog or policy configuration.") from exc
    _limiter = SlidingWindowLimiter(settings.rate_limit_per_minute)
    yield


app = FastAPI(
    title="From My Desk",
    description=(
        "Perspectives shaped by experience. Editorial publication with occasional "
        "interactive labs. Individual labs may use fictional data for teaching."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)

app.mount("/static/labs/001", StaticFiles(directory=str(LAB_001_STATIC)), name="lab001-static")
app.mount("/static", StaticFiles(directory=str(WEBSITE_DIR / "static")), name="static")
app.include_router(lab_router)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/evaluate", "/api/evaluate"} and request.method == "POST":
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
                        headers=SECURITY_HEADERS,
                    )
            content_length = request.headers.get("content-length")
            if content_length and content_length.isdigit() and int(content_length) > 16_384:
                return JSONResponse(
                    status_code=413,
                    content={
                        "reason_code": "invalid_request",
                        "reason": "Request body is too large.",
                    },
                    headers=SECURITY_HEADERS,
                )
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response


app.add_middleware(SecurityHeadersMiddleware)


def _page_context(request: Request, **extra: Any) -> Dict[str, Any]:
    settings = get_settings()
    host = request.url.hostname or ""
    is_test = os.environ.get("PYTEST_CURRENT_TEST") is not None
    labs = get_catalog()
    current = featured_lab(labs)
    return {
        "request": request,
        "github_url": settings.github_url,
        "newsletter_url": settings.newsletter_url,
        "labs": labs,
        "featured": current,
        "current_path": request.url.path,
        "footer_note": "From My Desk · Perspectives shaped by experience",
        "disclaimer": (
            "Educational simulation with fictional companies, agents, accounts, "
            "tickers, and thresholds. Not investment advice. No order is executed."
        ),
        "telemetry": public_telemetry_config(settings, host, is_test=is_test),
        **extra,
    }


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    response = await request_validation_exception_handler(request, exc)
    if request.url.path in {"/evaluate", "/api/evaluate"}:
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
    if slug != "know-your-agent":
        raise HTTPException(status_code=404, detail="This edition does not have an interactive page yet.")
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
