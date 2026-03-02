FROM python:3.11-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY gam_mcp /app/gam_mcp

RUN mkdir -p /gam-auth/cache

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "gam_mcp.server"]
