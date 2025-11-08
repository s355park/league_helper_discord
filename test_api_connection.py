"""Quick test to verify API connection before running bot."""
import asyncio
import httpx
from config import Config

async def test_api():
    """Test if the API is accessible."""
    base_url = Config.API_BASE_URL
    print(f"Testing API connection to: {base_url}")
    print("-" * 50)
    
    try:
        # Test health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health", timeout=5.0)
            if response.status_code == 200:
                print(f"✅ API is accessible!")
                print(f"   Response: {response.json()}")
                print(f"\n✅ Bot should be able to connect to: {base_url}")
                return True
            else:
                print(f"❌ API returned status code: {response.status_code}")
                return False
    except httpx.ConnectError as e:
        print(f"❌ Cannot connect to API at {base_url}")
        print(f"   Error: {str(e)}")
        print(f"\n🔧 Make sure FastAPI is running:")
        print(f"   python -m uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_api())

