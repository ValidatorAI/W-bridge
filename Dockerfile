FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache \
        bash \
    ca-certificates \
    curl

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv

COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

RUN chmod +x start.sh && \
    addgroup -S appgroup && \
    adduser -S appuser -G appgroup && \
    chown -R appuser:appgroup /app

USER appuser

CMD ["./start.sh"]
