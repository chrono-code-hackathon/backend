import os
from google import genai

class EmbeddingModel:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        return cls._instance

    async def get_embedding(self, texts: list[str]) -> list[float]:
        try:
            response = self._client.models.embed_content(
                model="text-embedding-004",
                contents=texts,
            )
            return response.embeddings
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

embedding_model = EmbeddingModel()

async def get_text_embedding(texts: list[str]) -> list[float]:
    """
    Generates a text embedding for the given text using the Gemini API.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding.
    """
    return await embedding_model.get_embedding(texts)