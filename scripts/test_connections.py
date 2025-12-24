"""
Health check script for FinSightAI services
Tests connectivity to all databases and external services
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2
from redis import Redis
import weaviate
from weaviate.classes.init import Auth
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config as NebulaConfig
from minio import Minio
from openai import OpenAI

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header():
    """Print test header"""
    print("\n" + "="*70)
    print(f"{CYAN}{BOLD}  FinSightAI - Service Health Check{RESET}")
    print("="*70 + "\n")


def print_result(service: str, status: bool, message: str = ""):
    """Print test result with color coding"""
    icon = f"{GREEN}✅{RESET}" if status else f"{RED}❌{RESET}"
    status_text = f"{GREEN}OK{RESET}" if status else f"{RED}FAILED{RESET}"
    
    print(f"{icon} {service:20s} [{status_text}]")
    if message:
        prefix = "   └─ " if not status else "   ℹ️  "
        print(f"{prefix}{message}")


def check_postgres() -> Tuple[bool, str]:
    """Test PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "finsight"),
            user=os.getenv("POSTGRES_USER", "finsight_user"),
            password=os.getenv("POSTGRES_PASSWORD", "secure_password")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, f"Connected - {version.split(',')[0]}"
    except Exception as e:
        return False, str(e)


def check_redis() -> Tuple[bool, str]:
    """Test Redis connection"""
    try:
        client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True
        )
        client.ping()
        info = client.info()
        return True, f"Connected - Redis {info['redis_version']}"
    except Exception as e:
        return False, str(e)


def check_weaviate() -> Tuple[bool, str]:
    """Test Weaviate connection"""
    try:
        client = weaviate.connect_to_local(
            host="localhost",
            port=8080
        )
        if client.is_ready():
            meta = client.get_meta()
            version = meta.get('version', 'unknown')
            client.close()
            return True, f"Connected - Weaviate {version}"
        else:
            return False, "Service not ready"
    except Exception as e:
        return False, str(e)


def check_nebula() -> Tuple[bool, str]:
    """Test NebulaGraph connection"""
    try:
        config = NebulaConfig()
        config.max_connection_pool_size = 2
        
        connection_pool = ConnectionPool()
        connection_pool.init(
            [(os.getenv("NEBULA_HOST", "localhost"), 
              int(os.getenv("NEBULA_PORT", "9669")))],
            config
        )
        
        session = connection_pool.get_session(
            os.getenv("NEBULA_USER", "root"),
            os.getenv("NEBULA_PASSWORD", "nebula")
        )
        
        result = session.execute("SHOW HOSTS;")
        if result.is_succeeded():
            connection_pool.close()
            return True, "Connected - NebulaGraph cluster active"
        else:
            connection_pool.close()
            return False, result.error_msg()
    except Exception as e:
        return False, str(e)


def check_minio() -> Tuple[bool, str]:
    """Test MinIO connection"""
    try:
        endpoint = os.getenv("S3_ENDPOINT", "localhost:9000").replace("http://", "").replace("https://", "")
        
        client = Minio(
            endpoint,
            access_key=os.getenv("S3_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("S3_SECRET_KEY", "minioadmin"),
            secure=os.getenv("S3_USE_SSL", "false").lower() == "true"
        )
        
        # List buckets to test connection
        buckets = client.list_buckets()
        bucket_name = os.getenv("S3_BUCKET", "finsight-documents")
        
        # Create bucket if it doesn't exist
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            return True, f"Connected - Bucket '{bucket_name}' created"
        
        return True, f"Connected - {len(buckets)} buckets found"
    except Exception as e:
        return False, str(e)


def check_openai() -> Tuple[bool, str]:
    """Test OpenAI API connection"""
    try:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key == "sk-your-api-key-here":
            return False, "API key not configured"
        
        client = OpenAI(api_key=api_key)
        
        # Test with a simple embedding call (cheaper than completion)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test"
        )
        
        if response.data and len(response.data) > 0:
            dim = len(response.data[0].embedding)
            return True, f"Connected - Embedding dimension: {dim}"
        
        return False, "No response from API"
    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            return False, "Invalid API key"
        return False, error_msg[:100]


def check_services():
    """Check all service health"""
    print_header()
    
    services = {
        "PostgreSQL": check_postgres,
        "Redis": check_redis,
        "Weaviate": check_weaviate,
        "NebulaGraph": check_nebula,
        "MinIO": check_minio,
        "OpenAI API": check_openai,
    }
    
    results = {}
    
    for service_name, check_func in services.items():
        success, message = check_func()
        results[service_name] = success
        print_result(service_name, success, message)
    
    # Print summary
    print("\n" + "="*70)
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    if failed == 0:
        print(f"{GREEN}{BOLD}✅ All services are healthy! ({passed}/{total}){RESET}")
    else:
        print(f"{YELLOW}{BOLD}⚠️  {passed}/{total} services healthy, {failed} failed{RESET}")
    
    print("="*70 + "\n")
    
    if failed > 0:
        print(f"{YELLOW}💡 Troubleshooting tips:{RESET}")
        print("   1. Make sure Docker Desktop is running")
        print("   2. Run: docker-compose up -d")
        print("   3. Wait 30-60 seconds for services to initialize")
        print("   4. Check logs: docker-compose logs")
        print()
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = check_services()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted{RESET}")
        sys.exit(1)
