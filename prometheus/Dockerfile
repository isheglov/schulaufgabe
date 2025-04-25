FROM prom/prometheus:latest

# Copy the Prometheus configuration template
COPY prometheus.yml /etc/prometheus/prometheus.yml.template

# Create a wrapper script to replace environment variables and start Prometheus
USER root
RUN echo '#!/bin/sh' > /bin/start-prometheus.sh && \
    echo 'set -e' >> /bin/start-prometheus.sh && \
    echo 'sed "s/\${PROMETHEUS_METRICS_USERNAME}/$PROMETHEUS_METRICS_USERNAME/g; s/\${PROMETHEUS_METRICS_PASSWORD}/$PROMETHEUS_METRICS_PASSWORD/g" /etc/prometheus/prometheus.yml.template > /etc/prometheus/prometheus.yml' >> /bin/start-prometheus.sh && \
    echo 'exec /bin/prometheus "$@"' >> /bin/start-prometheus.sh && \
    chmod +x /bin/start-prometheus.sh && \
    mkdir -p /prometheus && \
    chown -R nobody:nobody /prometheus /etc/prometheus /bin/start-prometheus.sh

# Switch back to non-root user
USER nobody

# Expose Prometheus web UI on port 9090
EXPOSE 9090

# Use our custom start script as the entrypoint
ENTRYPOINT ["/bin/start-prometheus.sh"]

# Start Prometheus with the configuration
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/usr/share/prometheus/console_libraries", \
     "--web.console.templates=/usr/share/prometheus/consoles", \
     "--web.enable-lifecycle"]
