FROM python:3.9-slim

WORKDIR /app

# Install dependencies (numba needs gcc and g++)
RUN apt-get update && apt-get install -y gcc g++ libc-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

COPY src/ src/
# Make sure python module imports work correctly
ENV PYTHONPATH=/app

# By default run a node
CMD ["python", "-m", "src.network.node"]
