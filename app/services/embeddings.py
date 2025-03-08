from google import genai
from app.config.settings import settings

class EmbeddingModel:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            cls._model = genai.GenerativeModel('text-embedding-005')  # https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text-embeddings-api#model_versions
        return cls._instance

    async def get_embedding(self, text: str) -> list[float]:
        try:
            response = self._model.embed(text)
            return response.embedding.values
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

embedding_model = EmbeddingModel()

async def get_text_embedding(text: str) -> list[float]:
    """
    Generates a text embedding for the given text using the Gemini API.

    Args:
        text: The text to embed.

    Returns:
        A list of floats representing the embedding.
    """
    return await embedding_model.get_embedding(text)
