import logging
from neo4j import Driver

logger = logging.getLogger("chickensoup.neo4j.schema")

NODE_LABELS = [
    "Person", "Place", "Concept", "QuantumPlatform", 
    "Algorithm", "Event", "Object", "Project", "Entity", "Paper"
]

def initialize_schema(driver: Driver) -> None:
    """
    Initializes constraints and indices in Neo4j for the various node types.
    """
    logger.info("Initializing Neo4j schema indices and constraints...")
    
    with driver.session() as session:
        # Create uniqueness constraints for names
        for label in NODE_LABELS:
            constraint_name = f"uniq_{label.lower()}_name"
            # In Neo4j 5.x, the syntax is:
            # CREATE CONSTRAINT constraint_name IF NOT EXISTS FOR (n:Label) REQUIRE n.name IS UNIQUE
            query = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label}) REQUIRE n.name IS UNIQUE
            """
            try:
                session.run(query)
                logger.debug(f"Ensured uniqueness constraint for {label}")
            except Exception as e:
                logger.warning(f"Could not create constraint for {label}: {e}. Standard index may be used.")

        # Create additional indexes for rapid lookup on common fields like confidence or date
        try:
            session.run("CREATE INDEX IF NOT EXISTS FOR (n:Event) ON (n.date)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.type)")
            logger.info("Neo4j schema constraints and indices initialized successfully.")
        except Exception as e:
            logger.warning(f"Error creating secondary indexes: {e}")
