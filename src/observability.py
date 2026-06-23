import logging
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
try:
    provider = TracerProvider()
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
except Exception as e:
    logger.debug(f"TracerProvider already initialized or failed: {e}")

tracer: Tracer = trace.get_tracer("chickensoup.tracer")

# Set up metrics
try:
    metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    meter_provider = MeterProvider(metric_readers=[metric_reader])
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
