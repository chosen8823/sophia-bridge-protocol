FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY mesh ./mesh
CMD ["python", "-m", "mesh.node"]
