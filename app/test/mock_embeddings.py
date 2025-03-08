import asyncio
from app.services.embeddings import get_text_embedding

async def main():
    test_text = "This is a test sentence for embedding."
    try:
        embedding = await get_text_embedding(test_text)
        print("Embedding generated successfully:")
        print(embedding)
        print(f"Embedding length: {len(embedding)}")
        assert len(embedding) > 0, "Embedding should not be empty"
    except Exception as e:
        print(f"Error during embedding generation: {e}")

if __name__ == "__main__":
    asyncio.run(main())

