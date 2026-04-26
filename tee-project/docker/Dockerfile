FROM python:3.11-slim AS builder
WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime
ENV PORT=8000 NO_LOGGING=true ENCLAVE_SIMULATION=true PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd -m -u 1000 teeuser
COPY --from=builder /root/.local /home/teeuser/.local
COPY backend/ .
RUN chown -R teeuser:teeuser /app
USER teeuser
ENV PATH=/home/teeuser/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
