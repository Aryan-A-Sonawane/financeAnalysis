"""Database initialization script."""

import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.db.nebula import nebula_client
from app.db.postgres import init_db as init_postgres
from app.db.weaviate import weaviate_client
from app.models.graph_schema import get_all_schema_statements
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def setup_postgres():
    """Initialize PostgreSQL database."""
    logger.info("Initializing PostgreSQL...")
    try:
        await init_postgres()
        logger.info("PostgreSQL initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize PostgreSQL", error=str(e), exc_info=True)
        raise


async def setup_nebula():
    """Initialize NebulaGraph schema."""
    logger.info("Initializing NebulaGraph...")
    try:
        await nebula_client.connect()
        
        # Execute schema statements
        statements = get_all_schema_statements()
        
        for i, stmt in enumerate(statements):
            try:
                logger.info(f"Executing statement {i+1}/{len(statements)}")
                await nebula_client.execute(stmt)
            except Exception as e:
                # Some statements might fail if already exist, log but continue
                logger.warning(f"Statement {i+1} failed", error=str(e))
        
        logger.info("NebulaGraph schema initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize NebulaGraph", error=str(e), exc_info=True)
        raise
    finally:
        await nebula_client.close()


async def setup_weaviate():
    """Initialize Weaviate schema."""
    logger.info("Initializing Weaviate...")
    try:
        await weaviate_client.connect()
        await weaviate_client.create_schema()
        logger.info("Weaviate schema initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Weaviate", error=str(e), exc_info=True)
        raise
    finally:
        await weaviate_client.close()


async def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize databases")
    parser.add_argument("--postgres", action="store_true", help="Initialize PostgreSQL")
    parser.add_argument("--nebula", action="store_true", help="Initialize NebulaGraph")
    parser.add_argument("--weaviate", action="store_true", help="Initialize Weaviate")
    parser.add_argument("--all", action="store_true", help="Initialize all databases")
    
    args = parser.parse_args()
    
    if args.all or (not args.postgres and not args.nebula and not args.weaviate):
        # Initialize all if no specific option given
        await setup_postgres()
        await setup_nebula()
        await setup_weaviate()
    else:
        if args.postgres:
            await setup_postgres()
        if args.nebula:
            await setup_nebula()
        if args.weaviate:
            await setup_weaviate()
    
    logger.info("Database initialization complete")


if __name__ == "__main__":
    asyncio.run(main())
