FROM python:3.11

# Install Tectonic and its dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic using the recommended way (with explicit move to ensure it's in PATH)
RUN curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh && \
    mv tectonic /usr/local/bin/ && \
    chmod +x /usr/local/bin/tectonic && \
    tectonic --version

# Set up the Python environment
WORKDIR /app
COPY requirements.txt .
COPY backend/requirements.txt ./backend-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r backend-requirements.txt && \
    pip install prometheus-client

# Copy the application
COPY . .

# Create a startup script to handle environment variables
RUN echo '#!/bin/bash\nuvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the application using the startup script
CMD ["/bin/bash", "/app/start.sh"]
