FROM prom/prometheus:latest

# Copy the Prometheus configuration file
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Set user to root temporarily to set proper permissions
USER root

# Set permissions for prometheus directories
RUN mkdir -p /prometheus && \
    chown -R nobody:nobody /prometheus /etc/prometheus

# Switch back to non-root user
USER nobody

# Expose Prometheus web UI on port 9090
EXPOSE 9090

# Start Prometheus with the configuration
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/usr/share/prometheus/console_libraries", \
     "--web.console.templates=/usr/share/prometheus/consoles", \
     "--web.enable-lifecycle"]
