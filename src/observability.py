import logging
from typing import Optional
from opentelemetry import trace, metrics
from opentelemetry.trace import Tracer
from opentelemetry.metrics import Meter, Counter, Histogram
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider

logger = logging.getLogger("chickensoup.observability")

# Set up tracing — no console exporter to avoid log noise
try:
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
except Exception as e:
    logger.debug(f"TracerProvider already initialized or failed: {e}")

tracer: Tracer = trace.get_tracer("chickensoup.tracer")

# Set up metrics — no console exporter to avoid log noise
try:
    meter_provider = MeterProvider()
    metrics.set_meter_provider(meter_provider)
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

# Living Almanac metrics
pulse_runs_total: Counter = meter.create_counter(
    name="pulse_runs_total",
    description="Number of pulse runs by status",
    unit="1"
)

pulse_latency_seconds: Histogram = meter.create_histogram(
    name="pulse_latency_seconds",
    description="Pulse execution latency",
    unit="s"
)

budget_spent_usd: Counter = meter.create_counter(
    name="budget_spent_usd",
    description="Total budget spent in USD",
    unit="1"
)

wavefunction_state_total: Counter = meter.create_counter(
    name="wavefunction_state_total",
    description="Wavefunction scoring by state label",
    unit="1"
)

divergence_risk_histogram: Histogram = meter.create_histogram(
    name="divergence_risk",
    description="Divergence risk distribution",
    unit="1"
)

tribunal_runs_total: Counter = meter.create_counter(
    name="tribunal_runs_total",
    description="Tribunal runs by trigger type",
    unit="1"
)

almanac_generated_total: Counter = meter.create_counter(
    name="almanac_generated_total",
    description="Almanac generation runs by status",
    unit="1"
)

almanac_generation_duration: Histogram = meter.create_histogram(
    name="almanac_generation_duration_seconds",
    description="Almanac generation duration",
    unit="s"
)

# LLM client metrics
llm_calls_total: Counter = meter.create_counter(
    name="llm_calls_total",
    description="LLM API calls by stage and status",
    unit="1"
)

llm_parse_failures_total: Counter = meter.create_counter(
    name="llm_parse_failures_total",
    description="LLM response parse failures by error type",
    unit="1"
)

llm_semaphore_wait_seconds: Histogram = meter.create_histogram(
    name="llm_semaphore_wait_seconds",
    description="Time spent waiting for LLM semaphore",
    unit="s"
)

llm_cache_hits_total: Counter = meter.create_counter(
    name="llm_cache_hits_total",
    description="LLM response cache hits",
    unit="1"
)
