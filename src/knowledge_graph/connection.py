import logging
from neo4j import GraphDatabase, Driver
from src.config import settings

logger = logging.getLogger("chickensoup.neo4j.connection")

class Neo4jConnection:
    def __init__(self):
        self._driver: Driver | None = None

    def connect(self) -> Driver:
        if not self._driver:
            try:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                # Test connectivity
                self._driver.verify_connectivity()
                logger.info("Successfully connected to Neo4j.")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j at {settings.NEO4J_URI}: {e}")
                raise e
        return self._driver

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed.")

    def get_driver(self) -> Driver:
        if not self._driver:
            return self.connect()
        return self._driver

    def check_health(self) -> bool:
        if not self._driver:
            try:
                self.connect()
            except Exception:
                return False
        try:
            # Run a lightweight query to verify connectivity
            with self._driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            logger.warning(f"Neo4j health check failed: {e}")
            return False

neo4j_conn = Neo4jConnection()
