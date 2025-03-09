from typing import List, Dict, Any, Optional
from app.models.models_AI import Document
import chromadb
from chromadb.errors import InvalidCollectionException
from app.logger.logger import logger

chroma_client = chromadb.Client()

def get_subcommit_collection(collection_name: str):
    """
    Get or create a ChromaDB collection with the given name.
    
    Args:
        collection_name: Name of the collection to get or create
        
    Returns:
        The ChromaDB collection
    """
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except InvalidCollectionException:
        # Collection doesn't exist, create it
        collection = chroma_client.create_collection(name=collection_name)
    return collection

def collection_exists(collection_name: str) -> bool:
    """
    Check if a ChromaDB collection with the given name exists.
    
    Args:
        collection_name: Name of the collection to check
        
    Returns:
        Boolean indicating whether the collection exists
    """
    try:
        chroma_client.get_collection(name=collection_name)
        return True
    except InvalidCollectionException:
        return False
    except Exception as e:
        logger.error(f"Error checking if collection exists: {e}")
        return False

def insert_document(documents: List[Document], collection_name: str = "subcommit_vectors"):
    """
    Insert a list of documents into ChromaDB.
    
    Args:
        documents: List of Document objects to insert
        collection_name: Name of the collection to insert into (default: "subcommit_vectors")
        
    Returns:
        Dictionary with status and message
    """
    try:
        # Get or create the specified collection
        collection = get_subcommit_collection(collection_name)
        
        # Extract data from documents
        vectors = [doc.vector for doc in documents]
        ids = [str(doc.subcommit_id) for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Add documents to collection
        collection.add(
            embeddings=vectors,
            metadatas=metadatas,
            ids=ids
        )
        
        return {"status": "success", "message": f"Successfully inserted {len(documents)} documents into collection {collection_name}"}
    except Exception as e:
        logger.error(f"Error inserting documents into ChromaDB: {e}")
        return {"status": "error", "error": str(e)}

def get_k_neighbors(collection_name: str, vector: List[float], k: int) -> Dict[str, Any]:
    """
    Get k nearest neighbors to the given vector from ChromaDB.
    
    Args:
        collection_name: Name of the collection to query
        vector: The embedding vector to find neighbors for
        k: Number of neighbors to return
        
    Returns:
        Dictionary containing the query results
    """
    try:
        # Get the collection
        collection = get_subcommit_collection(collection_name)
        
        # Query the collection
        results = collection.query(
            query_embeddings=[vector],
            n_results=k,
            include=["metadatas", "distances", "documents"]
        )
        
        # Process results
        neighbors = []
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                # Extract data for this result
                doc_id = results['ids'][0][i]
                metadata = results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {}
                distance = results['distances'][0][i] if 'distances' in results and results['distances'] else None
                
                # Get the actual subcommit_id from metadata if available
                subcommit_id = metadata.get("subcommit_id", doc_id)
                
                # Create a result object with the necessary information
                neighbor = {
                    "id": doc_id,
                    "subcommit_id": subcommit_id,
                    "metadata": metadata,
                    "distance": distance,
                    "similarity_score": 1.0 - distance if distance is not None else None
                }
                neighbors.append(neighbor)
        
        return {"results": neighbors}
    except Exception as e:
        logger.error(f"Error querying ChromaDB: {e}")
        return {"error": str(e)}
