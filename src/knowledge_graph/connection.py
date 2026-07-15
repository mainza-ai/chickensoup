import logging
import time
import threading
from neo4j import GraphDatabase, Driver
from src.config import settings

logger = logging.getLogger("chickensoup.neo4j.connection")


class Neo4jCircuitBreaker:
    """Circuit breaker for Neo4j connections to prevent cascade failures."""

    def __init__(self, threshold: int = 3, recovery_timeout: float = 30.0):
        self._threshold = threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._open = False
        self._lock = threading.Lock()

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self._threshold:
                self._open = True
                logger.warning(f"Neo4j circuit breaker opened after {self._failure_count} failures")

    def record_success(self):
        with self._lock:
            self._failure_count = 0
            self._open = False

    def is_available(self) -> bool:
        with self._lock:
            if not self._open:
                return True
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._open = False
                self._failure_count = 0
                logger.info("Neo4j circuit breaker half-open — allowing probe")
                return True
            return False

    def reset(self):
        with self._lock:
            self._failure_count = 0
            self._open = False


class Neo4jConnection:
    def __init__(self):
        self._driver: Driver | None = None
        self._circuit_breaker = Neo4jCircuitBreaker()
        self._lock = threading.Lock()

    def connect(self) -> Driver | None:
        if not self._circuit_breaker.is_available():
            logger.warning("Neo4j circuit breaker is open — skipping connection attempt")
            return None
        with self._lock:
            if self._driver:
                try:
                    self._driver.verify_connectivity()
                    self._circuit_breaker.record_success()
                    return self._driver
                except Exception:
                    self._close_driver()
            try:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                    max_connection_pool_size=10,
                    connection_timeout=10,
                )
                self._driver.verify_connectivity()
                self._circuit_breaker.record_success()
                logger.info("Connected to Neo4j successfully.")
                return self._driver
            except Exception as e:
                self._circuit_breaker.record_failure()
                logger.error(f"Failed to connect to Neo4j: {e}")
                self._driver = None
                return None

    def _close_driver(self):
        if self._driver:
            try:
                self._driver.close()
            except Exception:
                pass
            self._driver = None

    def close(self):
        with self._lock:
            self._close_driver()

    def get_driver(self) -> Driver | None:
        if not self._driver:
            return self.connect()
        try:
            self._driver.verify_connectivity()
            return self._driver
        except Exception:
            logger.warning("Neo4j driver connection lost — reconnecting")
            self._close_driver()
            return self.connect()

    def check_health(self) -> bool:
        driver = self.get_driver()
        if not driver:
            return False
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            self._circuit_breaker.record_success()
            return True
        except Exception as e:
            self._circuit_breaker.record_failure()
            logger.warning(f"Neo4j health check failed: {e}")
            return False


neo4j_conn = Neo4jConnection()
