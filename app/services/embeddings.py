import os
from google import genai
from app.logger.logger import logger
from app.config.settings import settings
from typing import List, Dict, Any
from app.models.models_commit import Commit, SubCommitAnalysis, SubCommitNeighbors
from app.models.models_AI import Document
from app.services.chromadb_service import insert_document, get_k_neighbors

class EmbeddingModel:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return cls._instance

    async def get_embedding(self, texts: list[str]) -> list[float]:
        try:
            response = self._client.models.embed_content(
                model="text-embedding-004",
                contents=texts,
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
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

def create_subcommit_text(subcommit: SubCommitAnalysis) -> str:
    """
    Create a text representation of a subcommit by concatenating relevant information.
    
    Args:
        subcommit: The subcommit to create text for
        
    Returns:
        A string representation of the subcommit
    """
    text_parts = [
        f"Title: {subcommit.title}",
        f"Idea: {subcommit.idea}",
        f"Description: {subcommit.description}",
        f"Type: {subcommit.type.value}"
    ]
    
    # Add file information
    file_texts = []
    for file in subcommit.files:
        file_text = f"File: {file.filename}"
        if file.patch:
            file_text += f", Patch: {file.patch}"
        file_texts.append(file_text)
    
    if file_texts:
        text_parts.append("Files: " + " | ".join(file_texts))
    
    return "\n".join(text_parts)

async def vectorize_subcommit(subcommit: SubCommitAnalysis) -> Document:
    """
    Vectorize a subcommit by creating a text representation and generating an embedding.
    
    Args:
        subcommit: The subcommit to vectorize
        
    Returns:
        A Document containing the subcommit's vector representation
    """
    # Create text representation
    text = create_subcommit_text(subcommit)
    
    # Generate embedding
    embedding = await get_text_embedding([text])
    
    if not embedding:
        raise ValueError("Failed to generate embedding for subcommit")
    
    # Create metadata
    metadata = {
        "commit_sha": subcommit.commit_sha,
        "title": subcommit.title,
        "type": subcommit.type.value,
    }
    
    # Create a unique ID for the subcommit
    # Using title as part of ID to make it more meaningful
    subcommit_id = f"{subcommit.commit_sha}_{subcommit.title.replace(' ', '_')[:30]}"
    
    # Create document
    document = Document(
        vector=embedding[0],  # First element since we only sent one text
        subcommit_id=subcommit_id,
        metadata=metadata
    )
    
    return document

async def store_subcommit_vector(subcommit: SubCommitAnalysis, collection_name: str = "default") -> Dict[str, Any]:
    """
    Vectorize and store a subcommit in the vector database.
    
    Args:
        subcommit: The subcommit to vectorize and store
        collection_name: The name of the collection to store the vector in
        
    Returns:
        A dictionary containing the status of the operation
    """
    document = await vectorize_subcommit(subcommit)
    result = insert_document(document, collection_name)
    return result

async def populate_collection(collection_name: str, subcommits: List[SubCommitAnalysis]) -> Dict[str, Any]:
    """
    Vectorize and store multiple subcommits in a new collection.
    
    Args:
        collection_name: The name of the collection to create and populate
        subcommits: List of SubCommitAnalysis objects to vectorize and store
        
    Returns:
        A dictionary containing the status of the operation
    """
    try:
        logger.info(f"Populating collection '{collection_name}' with {len(subcommits)} subcommits")
        
        documents = []
        for subcommit in subcommits:
            try:
                document = await vectorize_subcommit(subcommit)
                documents.append(document)
            except Exception as e:
                logger.error(f"Error vectorizing subcommit {subcommit.commit_sha}: {e}")
        
        # Insert all documents into the collection
        results = []
        for document in documents:
            result = insert_document(document, collection_name)
            results.append(result)
        
        success_count = sum(1 for r in results if not r.get("error"))
        
        return {
            "message": f"Successfully populated collection '{collection_name}' with {success_count}/{len(subcommits)} subcommits",
            "success_count": success_count,
            "total_count": len(subcommits),
            "collection_name": collection_name
        }
    
    except Exception as e:
        logger.error(f"Error populating collection '{collection_name}': {e}")
        return {"error": str(e)}

async def find_similar_subcommits(subcommit: SubCommitAnalysis, k: int = 5, collection_name: str = "default") -> SubCommitNeighbors:
    """
    Find k most similar subcommits to the given subcommit.
    
    Args:
        subcommit: The subcommit to find similar subcommits for
        k: Number of similar subcommits to return
        collection_name: The name of the collection to search in
        
    Returns:
        A SubCommitNeighbors object containing the similar subcommits
    """
    # Vectorize the subcommit
    document = await vectorize_subcommit(subcommit)
    
    # Find k nearest neighbors using the working get_k_neighbors function
    neighbors = get_k_neighbors(collection_name, document.vector, k)
    
    # Get all commit analyses from Supabase
    from app.services.supabase_service import get_commit_analysis
    
    # Convert neighbors to SubCommitAnalysis objects
    similar_subcommits = []
    
    for neighbor in neighbors:
        # Extract metadata from the neighbor
        subcommit_id = neighbor.subcommit_id
        
        # Use the complete analysis from Supabase
        similar_subcommit = get_commit_analysis(subcommit_id)
        similar_subcommits.append(similar_subcommit)
        
    # Return the neighbors
    return SubCommitNeighbors(subcommits=similar_subcommits)

async def find_similar_commits_by_text(text: str, k: int = 5, collection_name: str = "default") -> SubCommitNeighbors:
    """
    Find k most similar subcommits to the given text.
    
    Args:
        text: The text to find similar subcommits for
        k: Number of similar subcommits to return
        collection_name: The name of the collection to search in
        
    Returns:
        A SubCommitNeighbors object containing the similar subcommits
    """
    try:
        # Generate embedding for the input text
        embedding = await get_text_embedding([text])
        
        if not embedding:
            logger.error("Failed to generate embedding for input text")
            return SubCommitNeighbors(subcommits=[])
        
        # Find k nearest neighbors using the embedding
        neighbors = get_k_neighbors(collection_name, embedding[0], k)
        
        # Get commit analyses from Supabase
        from app.services.supabase_service import get_commit_analysis
        
        # Convert neighbors to SubCommitAnalysis objects
        similar_subcommits = []
        
        for neighbor in neighbors:
            # Extract subcommit_id from the neighbor
            subcommit_id = neighbor.subcommit_id
            
            # Use the complete analysis from Supabase
            similar_subcommit = get_commit_analysis(subcommit_id)
            similar_subcommits.append(similar_subcommit)
        
        # Return the neighbors
        return SubCommitNeighbors(subcommits=similar_subcommits)
    
    except Exception as e:
        logger.error(f"Error finding similar commits by text: {e}")
        return SubCommitNeighbors(subcommits=[])
