FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY netframe ./netframe
RUN groupadd --system lab && useradd --system --no-log-init --gid lab lab
USER lab
EXPOSE 9000
CMD ["python", "-m", "netframe.server", "--host", "0.0.0.0", "--port", "9000"]
