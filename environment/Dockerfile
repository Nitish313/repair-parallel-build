FROM python:3.12.7-slim-bookworm

# Toolchain for the C project. Versions pinned to Debian bookworm.
RUN apt-get update && \
    apt-get install -y --no-install-recommends make=4.3-4.1 gcc=4:12.2.0-3 libc6-dev binutils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/project
COPY project/ /app/project/
