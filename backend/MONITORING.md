# Schulaufgabetrain Backend Monitoring with Prometheus and Grafana Cloud

This guide explains how to use the Prometheus monitoring in the backend and connect it to Grafana Cloud.

## Monitoring Setup

The backend application has been instrumented with Prometheus metrics to monitor:

- Request counts and latencies
- LaTeX generation metrics (success/failure counts, generation time)
- PDF compilation metrics (success/failure counts, compilation time)
- Active user sessions

## Metrics Available

| Metric Name | Type | Description |
|-------------|------|-------------|
| `http_requests_total` | Counter | Total number of HTTP requests (labeled by method, endpoint, status) |
| `upload_total` | Counter | Total number of file uploads |
| `latex_generation_total` | Counter | LaTeX generations (labeled by success/failure) |
| `pdf_compilation_total` | Counter | PDF compilations (labeled by success/failure) |
| `request_processing_seconds` | Histogram | Request processing time (labeled by method, endpoint) |
| `latex_generation_seconds` | Histogram | Time spent generating LaTeX |
| `pdf_compilation_seconds` | Histogram | Time spent compiling PDF |
| `active_sessions` | Gauge | Number of active user sessions |

## Connecting to Grafana Cloud

1. Sign in to your Grafana Cloud account at https://grafana.com/
2. Navigate to your Prometheus instance details
3. Find your Prometheus remote write URL and API key
4. Update the `prometheus_config.yml` file with your credentials:
   ```yaml
   remote_write:
     - url: "https://<YOUR_PROMETHEUS_ENDPOINT>/api/prom/push"
       basic_auth:
         username: "<YOUR_GRAFANA_CLOUD_USERNAME>"
         password: "<YOUR_GRAFANA_CLOUD_API_KEY>"
   ```

## Running Prometheus Agent with Remote Write

To send your metrics to Grafana Cloud, you can use the Prometheus Agent:

```bash
# Install Prometheus (macOS)
brew install prometheus

# Run Prometheus in agent mode with your config
prometheus --config.file=prometheus_config.yml --enable-feature=agent
```

## Local Development

For local development, the FastAPI backend exposes metrics at `/metrics` endpoint which you can view in your browser at http://localhost:8000/metrics when running the backend.

## Deploying with Docker

In the Docker environment, update your Dockerfile to include the Prometheus client:

```dockerfile
# Add this to existing RUN command for pip
RUN pip install prometheus-client
```

## Building Dashboards in Grafana Cloud

Once your metrics are being sent to Grafana Cloud, you can create dashboards to monitor:

1. Request volume and latency
2. LaTeX generation success rate and performance
3. PDF compilation success rate and performance
4. Active user sessions

Example query for success rate of LaTeX generation:
```
sum(rate(latex_generation_total{status="success"}[5m])) / sum(rate(latex_generation_total[5m])) * 100
```

## Setting Up Alerts

Consider setting up alerts for:

1. High error rates: `sum(rate(latex_generation_total{status="failure"}[5m])) / sum(rate(latex_generation_total[5m])) > 0.1`
2. Long response times: `histogram_quantile(0.95, sum(rate(request_processing_seconds_bucket{endpoint="/api/generate-latex"}[5m])) by (le)) > 10`
3. Unexpected drops in traffic: `sum(rate(http_requests_total[5m])) < 0.1`
