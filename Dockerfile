FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# iptables is used only by the short-lived root entrypoint. The application
# and Chromium are started as an unprivileged user after the firewall is set.
RUN apt-get update \
    && apt-get install -y --no-install-recommends iptables util-linux \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/backend/requirements.txt \
    && python -m pip install --no-cache-dir "playwright==1.63.0" \
    && python -m playwright install --with-deps chromium

RUN useradd --uid 1000 --user-group --create-home --shell /usr/sbin/nologin pwuser

COPY --chown=pwuser:pwuser backend/__init__.py backend/main.py backend/security.py backend/scraper.py backend/analyzer.py backend/llm_analyzer.py /app/backend/
COPY --chown=pwuser:pwuser frontend/ /app/frontend/
COPY docker/api-entrypoint.sh /usr/local/bin/api-entrypoint.sh
RUN chmod 0755 /usr/local/bin/api-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/api-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
