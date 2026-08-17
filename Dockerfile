FROM python:3.12-slim

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

WORKDIR /srv

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY pyproject.toml /srv/pyproject.toml
COPY website /srv/website
COPY labs/001-know-your-agent/src /srv/labs/001-know-your-agent/src
COPY labs/001-know-your-agent/policies /srv/labs/001-know-your-agent/policies
COPY labs/001-know-your-agent/static /srv/labs/001-know-your-agent/static

RUN pip install --no-cache-dir .

ENV WEBSITE_TEMPLATE_DIR=/srv/website/app/templates
ENV WEBSITE_STATIC_DIR=/srv/website/app/static
ENV LAB_STATIC_DIR=/srv/labs/001-know-your-agent/static
ENV CATALOG_PATH=/srv/website/catalog/labs.yaml
ENV POLICY_DIR=/srv/labs/001-know-your-agent/policies
ENV APP_VERSION=0.3.0
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POSTHOG_ENABLED=false
ENV POSTHOG_KEY=
ENV POSTHOG_HOST=https://us.i.posthog.com

USER appuser
WORKDIR /srv
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=4)"

CMD ["sh", "-c", "uvicorn from_my_desk.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers"]
