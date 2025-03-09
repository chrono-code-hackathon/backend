from typing import List
from app.models.models_AI import Document
import chromadb
from chromadb.errors import InvalidCollectionException  # Import the specific exception

chroma_client = chromadb.Client()

def get_subcommit_collection():
    # Get or create the collection if it doesn't exist
    try:
        collection = chroma_client.get_collection(name="subcommit_vectors")
    except InvalidCollectionException:  # Catch the specific exception
        # Collection doesn't exist, create it
        collection = chroma_client.create_collection(name="subcommit_vectors")
    return collection

def insert_document(document: Document): # Asociamos el vector al subcommit_id
    collection = get_subcommit_collection()
    
    # Use the vector from the Document model based on the context
    vector = document.vector
    subcommit_id = document.subcommit_id   
    metadata = document.metadata
    
    collection.add(
        embeddings=[vector],
        metadatas=[metadata],
        ids=[subcommit_id] 
    )
    
    return {"status": "success", "message": f"Document with subcommit_id {subcommit_id} inserted successfully"}

def get_k_neighbors(vector: List[float], k: int) -> List[Document]:
    """
    Get k nearest neighbors to the given vector from ChromaDB.
    
    Args:
        vector: The embedding vector to find neighbors for
        k: Number of neighbors to return
        
    Returns:
        List of Document objects representing the nearest neighbors
    """
    # Get the collection
    collection = get_subcommit_collection()
    
    # Query the collection using the vector directly
    results = collection.query(
        query_embeddings=[vector],  # Pass the vector directly
        n_results=k,                # Number of results to return
        include=["documents", "metadatas", "distances"]  # Include all relevant data
    )
    
    # Process results into Document objects
    documents = []
    if results and results['ids'] and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            # Extract data for this result
            doc_id = results['ids'][0][i]
            content = results['documents'][0][i] if 'documents' in results and results['documents'] else ""
            metadata = results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {}
            distance = results['distances'][0][i] if 'distances' in results and results['distances'] else None
            
            # Create Document object with all required fields
            doc = Document(
                id=doc_id,
                content=content,
                # Use the subcommit_id from metadata or the doc_id as fallback
                subcommit_id=metadata.get("subcommit_id") or doc_id,
                # Include the original vector or a placeholder
                vector=[0.0],  # You might need to query the vector separately or use a placeholder
                # Include the metadata or an empty dict
                metadata=metadata or {},
                # Optional: include similarity score
                similarity_score=1.0 - distance if distance is not None else None
            )
            documents.append(doc)
    
    return documents
    
