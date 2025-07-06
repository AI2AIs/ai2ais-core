# scripts/setup_qdrant.py
import asyncio
from app.core.ai.memory.vector_store import vector_store
from app.core.ai.memory.embeddings import embedding_service

async def setup_qdrant():
    """Initialize Qdrant collection"""
    
    print("🚀 Setting up Qdrant...")
    
    try:
        # Test connection
        connected = await vector_store.test_connection()
        if not connected:
            print("❌ Cannot connect to Qdrant. Is it running?")
            return False
        
        print("✅ Qdrant connected")
        
        # Test embedding service
        test_embedding = await embedding_service.embed_text("test")
        print(f"✅ Embeddings working: {len(test_embedding)} dimensions")
        
        print("🎉 Qdrant setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(setup_qdrant())