FROM prom/prometheus:latest

# Install dependencies for environment variable substitution
USER root
RUN apt-get update && apt-get install -y gettext-base && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the Prometheus configuration template
COPY prometheus.yml /etc/prometheus/prometheus.yml.template

# Set permissions for prometheus directories
RUN mkdir -p /prometheus && \
    chown -R nobody:nobody /prometheus /etc/prometheus

# Create startup script to handle environment variable substitution
RUN echo '#!/bin/sh\n\
envsubst < /etc/prometheus/prometheus.yml.template > /etc/prometheus/prometheus.yml\n\
exec /bin/prometheus "$@"' > /usr/local/bin/start-prometheus.sh && \
    chmod +x /usr/local/bin/start-prometheus.sh

# Switch back to non-root user
USER nobody

# Expose Prometheus web UI on port 9090
EXPOSE 9090

# Start Prometheus with the configuration
ENTRYPOINT ["/usr/local/bin/start-prometheus.sh"]
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/usr/share/prometheus/console_libraries", \
     "--web.console.templates=/usr/share/prometheus/consoles", \
     "--web.enable-lifecycle"]
