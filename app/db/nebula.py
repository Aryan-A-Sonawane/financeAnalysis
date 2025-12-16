"""NebulaGraph connection pool and query utilities."""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool
from nebula3.gclient.net.SessionPool import SessionPool

from app.config import settings
from app.models.graph_schema import QUERIES
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NebulaGraphClient:
    """NebulaGraph client wrapper."""

    def __init__(self):
        """Initialize NebulaGraph client."""
        self.config = Config()
        self.config.max_connection_pool_size = settings.NEBULA_POOL_SIZE
        self.connection_pool: Optional[ConnectionPool] = None
        self.session_pool: Optional[SessionPool] = None

    async def connect(self) -> None:
        """Initialize connection pool."""
        try:
            # Initialize connection pool
            self.connection_pool = ConnectionPool()
            self.connection_pool.init(
                [(settings.NEBULA_HOST, settings.NEBULA_PORT)],
                self.config
            )

            # Initialize session pool
            self.session_pool = SessionPool(
                settings.NEBULA_USER,
                settings.NEBULA_PASSWORD,
                settings.NEBULA_SPACE,
                [(settings.NEBULA_HOST, settings.NEBULA_PORT)]
            )

            logger.info(
                "NebulaGraph connection established",
                host=settings.NEBULA_HOST,
                port=settings.NEBULA_PORT,
                space=settings.NEBULA_SPACE
            )
        except Exception as e:
            logger.error("Failed to connect to NebulaGraph", error=str(e), exc_info=True)
            raise

    async def close(self) -> None:
        """Close connection pool."""
        if self.connection_pool:
            self.connection_pool.close()
        if self.session_pool:
            self.session_pool.close()
        logger.info("NebulaGraph connection closed")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a query."""
        if not self.session_pool:
            raise RuntimeError("NebulaGraph connection not initialized")

        try:
            # Replace parameters in query
            if params:
                for key, value in params.items():
                    if isinstance(value, str):
                        query = query.replace(f"${key}", f'"{value}"')
                    else:
                        query = query.replace(f"${key}", str(value))

            # Execute query
            result = self.session_pool.execute(query)
            
            if not result.is_succeeded():
                error_msg = result.error_msg()
                logger.error("NebulaGraph query failed", query=query, error=error_msg)
                raise RuntimeError(f"Query failed: {error_msg}")

            return result
        except Exception as e:
            logger.error("Error executing NebulaGraph query", error=str(e), exc_info=True)
            raise

    async def execute_named_query(
        self, query_name: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a named query from graph_schema."""
        if query_name not in QUERIES:
            raise ValueError(f"Unknown query: {query_name}")
        
        query = QUERIES[query_name]
        return await self.execute(query, params)

    async def insert_node(
        self, tag: str, vid: str, properties: Dict[str, Any]
    ) -> None:
        """Insert a node."""
        props_str = ", ".join(
            f"{k}: {self._format_value(v)}" for k, v in properties.items()
        )
        query = f'INSERT VERTEX {tag} ({props_str}) VALUES "{vid}":({props_str});'
        await self.execute(query)

    async def insert_edge(
        self,
        edge_type: str,
        src_vid: str,
        dst_vid: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert an edge."""
        if properties:
            props_str = ", ".join(
                f"{k}: {self._format_value(v)}" for k, v in properties.items()
            )
            query = f'INSERT EDGE {edge_type} ({props_str}) VALUES "{src_vid}"->"{dst_vid}":({props_str});'
        else:
            query = f'INSERT EDGE {edge_type} () VALUES "{src_vid}"->"{dst_vid}":();'
        
        await self.execute(query)

    def _format_value(self, value: Any) -> str:
        """Format value for NebulaGraph query."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif value is None:
            return "NULL"
        else:
            return str(value)


# Global client instance
nebula_client = NebulaGraphClient()


async def get_nebula_client() -> NebulaGraphClient:
    """Get NebulaGraph client instance."""
    if not nebula_client.connection_pool:
        await nebula_client.connect()
    return nebula_client
