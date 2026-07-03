import logging
import os
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.trace import Tracer
from opentelemetry.metrics import Meter, Counter, Histogram
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

logger = logging.getLogger("chickensoup.observability")

# Set up tracing
_otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
try:
    provider = TracerProvider()
    if _otel_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            processor = SimpleSpanProcessor(OTLPSpanExporter(endpoint=_otel_endpoint, insecure=True))
            logger.info(f"OTLP trace exporter configured: {_otel_endpoint}")
        except ImportError:
            logger.warning("opentelemetry-exporter-otlp not installed; falling back to console trace exporter")
            processor = SimpleSpanProcessor(ConsoleSpanExporter())
    else:
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        logger.debug("No OTEL_EXPORTER_OTLP_ENDPOINT set; using console trace exporter")
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
except Exception as e:
    logger.debug(f"TracerProvider already initialized or failed: {e}")

tracer: Tracer = trace.get_tracer("chickensoup.tracer")

# Set up metrics
try:
    try:
        from prometheus_client import start_http_server
        import threading
        _metrics_port = int(os.getenv("PROMETHEUS_METRICS_PORT", "8001"))
        t = threading.Thread(
            target=start_http_server,
            args=(_metrics_port,),
            daemon=True,
            name="prometheus-metrics",
        )
        t.start()
        logger.info(f"Prometheus metrics server started on port {_metrics_port}")
    except ImportError:
        logger.debug("prometheus_client not available; metrics will not be exposed via HTTP")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            logger.debug(f"Prometheus metrics server already running on port {_metrics_port}")
        else:
            raise

    reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    meter_provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
except Exception as e:
    logger.debug(f"MeterProvider already initialized or failed: {e}")

meter: Meter = metrics.get_meter("chickensoup.metrics")

# Application metrics
agent_loop_counter: Counter = meter.create_counter(
    name="agent_loop_executions",
    description="Number of times agent loop has executed",
    unit="1"
)

quantum_simulation_duration: Histogram = meter.create_histogram(
    name="quantum_simulation_duration_seconds",
    description="Duration of quantum spacetime simulation runs",
    unit="s"
)

cache_hits: Counter = meter.create_counter(
    name="cache_hits_total",
    description="Total cache hits",
    unit="1"
)

cache_misses: Counter = meter.create_counter(
    name="cache_misses_total",
    description="Total cache misses",
    unit="1"
)
