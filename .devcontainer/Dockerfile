# Dockerfile para instalar OS + FFmpeg
# Usamos la imagen oficial de Dev Containers para Python 3.11
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Evitamos diálogos interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Actualizamos el sistema e instalamos FFmpeg
RUN apt-get update && \
    apt-get -y install --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*