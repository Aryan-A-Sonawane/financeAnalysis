"""Quick health check and demo script."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def check_services():
    """Check if all services are accessible."""
    import httpx
    
    services = {
        "PostgreSQL": "postgresql://finsight_user:password@localhost:5432/finsight",
        "Redis": "localhost:6379",
        "MinIO": "http://localhost:9000",
        "NebulaGraph": "localhost:9669",
        "Weaviate": "http://localhost:8080",
    }
    
    print("=" * 60)
    print("FinSightAI Service Health Check")
    print("=" * 60)
    
    # Check HTTP services
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Weaviate
        try:
            response = await client.get("http://localhost:8080/v1/.well-known/ready")
            if response.status_code == 200:
                print("✅ Weaviate: Running")
            else:
                print(f"❌ Weaviate: Not ready (status {response.status_code})")
        except Exception as e:
            print(f"❌ Weaviate: Not accessible - {str(e)[:50]}")
        
        # MinIO
        try:
            response = await client.get("http://localhost:9000/minio/health/live")
            if response.status_code == 200:
                print("✅ MinIO: Running")
            else:
                print(f"❌ MinIO: Not ready (status {response.status_code})")
        except Exception as e:
            print(f"❌ MinIO: Not accessible - {str(e)[:50]}")
    
    # Check PostgreSQL
    try:
        from app.db.postgres import engine
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL: Connected")
    except Exception as e:
        print(f"❌ PostgreSQL: {str(e)[:50]}")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis: Connected")
    except Exception as e:
        print(f"❌ Redis: {str(e)[:50]}")
    
    # Check NebulaGraph
    try:
        from nebula3.gclient.net import ConnectionPool
        from nebula3.Config import Config
        
        config = Config()
        config.max_connection_pool_size = 1
        pool = ConnectionPool()
        pool.init([('localhost', 9669)], config)
        print("✅ NebulaGraph: Connected")
        pool.close()
    except Exception as e:
        print(f"❌ NebulaGraph: {str(e)[:50]}")
    
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start API: uvicorn app.main:app --reload")
    print("2. Open browser: http://localhost:8000/docs")
    print("3. Register user and test document upload")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_services())
