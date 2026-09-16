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
COPY labs/002-delegated-authority/src /srv/labs/002-delegated-authority/src
COPY labs/002-delegated-authority/policies /srv/labs/002-delegated-authority/policies
COPY labs/002-delegated-authority/examples /srv/labs/002-delegated-authority/examples
COPY labs/002-delegated-authority/static /srv/labs/002-delegated-authority/static
COPY labs/003-agent-access-control/src /srv/labs/003-agent-access-control/src
COPY labs/003-agent-access-control/policies /srv/labs/003-agent-access-control/policies
COPY labs/003-agent-access-control/examples /srv/labs/003-agent-access-control/examples
COPY labs/003-agent-access-control/static /srv/labs/003-agent-access-control/static
COPY labs/004-agent-escalation-boundary/src /srv/labs/004-agent-escalation-boundary/src
COPY labs/004-agent-escalation-boundary/policies /srv/labs/004-agent-escalation-boundary/policies
COPY labs/004-agent-escalation-boundary/examples /srv/labs/004-agent-escalation-boundary/examples
COPY labs/004-agent-escalation-boundary/static /srv/labs/004-agent-escalation-boundary/static
COPY labs/005-verifiable-action-receipts/src /srv/labs/005-verifiable-action-receipts/src
COPY labs/005-verifiable-action-receipts/policies /srv/labs/005-verifiable-action-receipts/policies
COPY labs/005-verifiable-action-receipts/examples /srv/labs/005-verifiable-action-receipts/examples
COPY labs/005-verifiable-action-receipts/static /srv/labs/005-verifiable-action-receipts/static

RUN pip install --no-cache-dir .

ENV WEBSITE_TEMPLATE_DIR=/srv/website/app/templates
ENV WEBSITE_STATIC_DIR=/srv/website/app/static
ENV LAB_STATIC_DIR=/srv/labs/001-know-your-agent/static
ENV LAB002_STATIC_DIR=/srv/labs/002-delegated-authority/static
ENV CATALOG_PATH=/srv/website/catalog/labs.yaml
ENV POLICY_DIR=/srv/labs/001-know-your-agent/policies
ENV LAB002_DATA_DIR=/srv/labs/002-delegated-authority/examples
ENV LAB002_POLICY_DIR=/srv/labs/002-delegated-authority/policies
ENV LAB003_STATIC_DIR=/srv/labs/003-agent-access-control/static
ENV LAB003_DATA_DIR=/srv/labs/003-agent-access-control/examples
ENV LAB003_POLICY_DIR=/srv/labs/003-agent-access-control/policies
ENV LAB004_STATIC_DIR=/srv/labs/004-agent-escalation-boundary/static
ENV LAB004_DATA_DIR=/srv/labs/004-agent-escalation-boundary/examples
ENV LAB004_POLICY_DIR=/srv/labs/004-agent-escalation-boundary/policies
ENV LAB005_STATIC_DIR=/srv/labs/005-verifiable-action-receipts/static
ENV LAB005_DATA_DIR=/srv/labs/005-verifiable-action-receipts/examples
ENV LAB005_POLICY_DIR=/srv/labs/005-verifiable-action-receipts/policies
ENV APP_VERSION=0.4.0
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
