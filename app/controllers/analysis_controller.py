from fastapi import APIRouter, HTTPException
from typing import List, Optional
import asyncio

from pydantic import BaseModel
from app.models.models_commit import ChatResponse, Commit, SubCommitAnalysis
from app.services.gemini import get_commit_analysis, analyze_commits_batch, answer_user_query_with_subcommits
from app.services.supabase_service import store_commit_analyses, get_all_commit_analyses
from app.config.settings import settings
from app.services import commits
from app.services.commits import AlreadyAnalyzedRepositoryError
from app.logger.logger import logger
from app.services.embeddings import get_text_embedding, create_subcommit_text
from app.services.chromadb_service import insert_document, get_k_neighbors
from app.models.models_AI import Document

router = APIRouter()

class CommitAnalysisRequest(BaseModel):
    repository_url: str
    access_token: Optional[str] = None

class UpdateAnalysisRequest(BaseModel):
    repository_url: str
    branch: Optional[str] = None
    path: Optional[str] = None

class EmbeddingSpaceRequest(BaseModel):
    repository_url: str

class QueryCommitsRequest(BaseModel):
    repository_id: str
    query: str
    k: int = 5

async def analyze_commit(commit: Commit) -> List[SubCommitAnalysis]:
    """
    Analyzes a single commit using Gemini.
    
    Parameters:
    - commit: Commit object to analyze
    
    Returns:
    - A list of analyses or an empty list if an error occurs
    """
    try:
        logger.info(f"Analyzing commit: {commit.sha}")
        if commit.files and len(commit.files) > 0:
            analysis_result = await get_commit_analysis(commit)
        else:
            logger.warning(f"Commit {commit.sha} has no files, skipping analysis")
            return []
        if analysis_result and analysis_result.analysis:
            logger.info(f"Successfully analyzed commit: {commit.sha}")
            return analysis_result.analysis
        else:
            logger.warning(f"No analyses generated for commit: {commit.sha}")
            return []
    except Exception as e:
        print(e)
        logger.error(f"Error analyzing commit {commit.sha}: {str(e)}")
        return []
@router.post("/analyze-commits")
async def analyze_commits(request: CommitAnalysisRequest):
    """
    Endpoint to analyze commits from a repository using Gemini and store the results in Supabase.
    
    Parameters:
    - repository_url: URL of the repository to analyze
    
    Returns:
    - A summary of the analysis and storage operation
    """
    try:
        logger.info(f"Received request to analyze commits from repository: {request.repository_url}")
        
        try:
            # Fetch commits from the repository
            list_commits = await commits.get_repository_commits(request.repository_url, request.access_token)

            # Handle the case where no commits are returned (either repo not found or no commits)
            if not list_commits:
                logger.warning(f"No commits found or repository not found: {request.repository_url}")
                return {
                    "status": "not_found",
                    "message": f"Repository {request.repository_url} not found or no new commits available.",
                    "analyses_count": 0
                }
            
            logger.info(f"Fetched {len(list_commits)} commits from repository: {request.repository_url}")
        
        except AlreadyAnalyzedRepositoryError as e:
            logger.warning(f"Repository {request.repository_url} has already been analyzed.")
            return {
                "status": "already_analyzed",
                "message": f"Repository {request.repository_url} has already been analyzed.",
                "analyses_count": 0
            }
        
        all_analyses: List[SubCommitAnalysis] = []
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
        logger.info(f"Using batch size: {batch_size}")
        
        # Create batches
        batches = [list_commits[i:i + batch_size] for i in range(0, len(list_commits), batch_size)]
        logger.info(f"Split commits into {len(batches)} batches")
        
        # Process all batches concurrently
        batch_tasks = [analyze_commits_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Combine all results
        for batch_result in batch_results:
            if batch_result:
                all_analyses.extend(batch_result)
        
        logger.info(f"Generated a total of {len(all_analyses)} analyses")
        
        # Store all analyses in Supabase
        if all_analyses:
            logger.info("Storing analyses in Supabase")
            storage_result = store_commit_analyses(all_analyses)
            
            if "error" in storage_result:
                logger.error(f"Error storing analyses in Supabase: {storage_result['error']}")
                return {
                    "status": "partial_success",
                    "message": f"Analyzed {len(list_commits)} commits, but encountered an error storing results.",
                    "error": storage_result["error"],
                    "analyses_count": len(all_analyses)
                }
            
            logger.info(f"Successfully stored {len(all_analyses)} analyses in Supabase")
            
            # Generate embeddings for the repository after analysis is complete
            logger.info(f"Generating embeddings for repository: {request.repository_url}")
            
            # Get repository ID from the analyses
            repo_id = None
            if all_analyses and hasattr(all_analyses[0], 'repo_id'):
                repo_id = all_analyses[0].repo_id
            else:
                # Get repo ID from Supabase if not available in analyses
                result = get_all_commit_analyses(request.repository_url)
                if "repo_id" in result:
                    repo_id = result["repo_id"]
            
            if not repo_id:
                logger.error("Repository ID not found for embedding generation")
                return {
                    "status": "partial_success",
                    "message": f"Successfully analyzed {len(list_commits)} commits and stored {len(all_analyses)} analyses, but failed to generate embeddings due to missing repository ID.",
                    "analyses_count": len(all_analyses)
                }
            
            # Process all embeddings concurrently
            async def process_analysis(analysis):
                # Prepare text for the analysis
                text = create_subcommit_text(analysis)
                
                # Generate embedding for the text
                embedding = await get_text_embedding([text])
                
                if embedding and embedding[0]:
                    # Create document with embedding
                    doc = Document(
                        vector=embedding[0],
                        subcommit_id=analysis.id,
                        metadata={
                            "subcommit_id": analysis.id,
                            "content": f"Title: {analysis.title}\nDescription: {analysis.description}\nIdea: {analysis.idea}",
                            "id": analysis.id,
                            "commit_sha": analysis.commit_sha,
                            "title": analysis.title,
                            "repo_id": repo_id
                        },
                    )
                    return doc
                else:
                    logger.warning(f"Failed to generate embedding for subcommit: {analysis.id}")
                    return None
            
            # Create tasks for all analyses at once
            tasks = [process_analysis(analysis) for analysis in all_analyses]
            
            # Process all analyses concurrently
            embedding_results = await asyncio.gather(*tasks)
            
            # Filter out None results
            documents = [doc for doc in embedding_results if doc is not None]
            
            logger.info(f"Created {len(documents)} documents with embeddings")
            
            # Insert all documents into ChromaDB at once
            collection_name = f"{repo_id}"
            insert_result = insert_document(documents, collection_name)
            if "error" in insert_result:
                logger.error(f"Error inserting documents into ChromaDB: {insert_result['error']}")
                return {
                    "status": "partial_success",
                    "message": f"Successfully analyzed {len(list_commits)} commits and stored {len(all_analyses)} analyses, but encountered an error creating embedding space: {insert_result['error']}",
                    "analyses_count": len(all_analyses),
                    "embeddings_count": 0
                }
            
            logger.info(f"Successfully created embedding space for {repo_id} with {len(documents)} embeddings")
            return {
                "status": "success",
                "message": f"Successfully analyzed {len(list_commits)} commits, stored {len(all_analyses)} analyses, and created embedding space with {len(documents)} embeddings.",
                "analyses_count": len(all_analyses),
                "embeddings_count": len(documents),
                "collection_name": collection_name
            }
        else:
            logger.warning("No analyses were generated for the commits.")
            return {
                "status": "warning",
                "message": f"Processed {len(list_commits)} commits, but no analyses were generated.",
                "analyses_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error in analyze_commits endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing commits: {str(e)}")

@router.post("/update-analysis")
async def update_analysis(request: UpdateAnalysisRequest):
    """
    Endpoint to analyze only new commits from a repository that has already been analyzed.
    
    Parameters:
    - repository_url: URL of the repository to analyze
    - branch: Optional branch to analyze (default is the repository's default branch)
    - path: Optional path to filter commits by
    
    Returns:
    - A summary of the analysis and storage operation
    """
    try:
        logger.info(f"Received request to analyze new commits from repository: {request.repository_url}")
        
        # Fetch only new commits from the repository
        list_commits = await commits.get_new_repository_commits(
            request.repository_url, 
            branch=request.branch, 
            path=request.path
        )
        
        # Filter commits for test purposes
        test_hashes = ["c7bbf95983af1ee41b6cec39dba64e3c8227f7bd", "2cab1a7de446f4fdf6efc4b8f465de89d0826cca"]
        list_commits = [commit for commit in list_commits if commit.sha in test_hashes]
        
        # Handle the case where no new commits are found
        if not list_commits:
            logger.info(f"No new commits found for repository: {request.repository_url}")
            return {
                "status": "success",
                "message": f"No new commits to analyze for repository {request.repository_url}.",
                "analyses_count": 0
            }
        
        logger.info(f"Fetched {len(list_commits)} new commits from repository: {request.repository_url}")
        
        all_analyses: List[SubCommitAnalysis] = []
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
        logger.info(f"Using batch size: {batch_size}")
        
        # Create batches
        batches = [list_commits[i:i + batch_size] for i in range(0, len(list_commits), batch_size)]
        logger.info(f"Split commits into {len(batches)} batches")
        
        # Process all batches concurrently
        batch_tasks = [analyze_commits_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Combine all results
        for batch_result in batch_results:
            if batch_result:
                all_analyses.extend(batch_result)
        
        logger.info(f"Generated a total of {len(all_analyses)} analyses")
        
        # Store all analyses in Supabase
        if all_analyses:
            logger.info("Storing analyses in Supabase")
            storage_result = store_commit_analyses(all_analyses)
            
            if "error" in storage_result:
                logger.error(f"Error storing analyses in Supabase: {storage_result['error']}")
                return {
                    "status": "partial_success",
                    "message": f"Analyzed {len(list_commits)} new commits, but encountered an error storing results.",
                    "error": storage_result["error"],
                    "analyses_count": len(all_analyses)
                }
            
            logger.info(f"Successfully stored {len(all_analyses)} analyses in Supabase")
            return {
                "status": "success",
                "message": f"Successfully analyzed {len(list_commits)} new commits and stored {len(all_analyses)} analyses.",
                "analyses_count": len(all_analyses)
            }
        else:
            logger.warning("No analyses were generated for the new commits.")
            return {
                "status": "warning",
                "message": f"Processed {len(list_commits)} new commits, but no analyses were generated.",
                "analyses_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error in update_analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing new commits: {str(e)}")

@router.post("/create-embedding-space")
async def create_embedding_space(request: EmbeddingSpaceRequest):
    """
    Endpoint to create an embedding space for a repository's commit analyses.
    
    Parameters:
    - repository_url: URL of the repository to create embedding space for
    
    Returns:
    - A summary of the embedding space creation operation
    """
    try:
        logger.info(f"Received request to create embedding space for repository: {request.repository_url}")
        
        # Get all commit analyses for the repository
        result = get_all_commit_analyses(request.repository_url)
        
        if "error" in result:
            logger.error(f"Error retrieving commit analyses: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Error retrieving commit analyses: {result['error']}")
        
        if not result.get("data"):
            logger.warning(f"No commit analyses found for repository: {request.repository_url}")
            return {
                "status": "warning",
                "message": f"No commit analyses found for repository {request.repository_url}.",
                "embeddings_count": 0
            }
        
        analyses = result["data"]
        repo_id = result.get("repo_id")
        if not repo_id:
            logger.error("Repository ID not found in result")
            raise HTTPException(status_code=500, detail="Repository ID not found")
        
        logger.info(f"Retrieved {len(analyses)} commit analyses for repository ID: {repo_id}")
        
        # Process all embeddings concurrently without batching
        import asyncio
        
        async def process_analysis(analysis):
            # Prepare text for the analysis
            text = create_subcommit_text(analysis)
            
            # Generate embedding for the text
            embedding = await get_text_embedding([text])
            
            if embedding and embedding[0]:
                # Create document with embedding
                doc = Document(
                    vector=embedding,
                    subcommit_id=analysis.id,
                    metadata={
                        "subcommit_id": analysis.id,
                        "content": f"Title: {analysis.title}\nDescription: {analysis.description}\nIdea: {analysis.idea}",
                        "id": analysis.id,
                        "commit_sha": analysis.commit_sha,
                        "title": analysis.title,
                        "repo_id": repo_id
                    },
                )
                return doc
            else:
                logger.warning(f"Failed to generate embedding for subcommit: {analysis.id}")
                return None
        
        # Create tasks for all analyses at once
        tasks = [process_analysis(analysis) for analysis in analyses]
        
        # Process all analyses concurrently
        results = await asyncio.gather(*tasks)
        
        # Filter out None results
        documents = [doc for doc in results if doc is not None]
        
        logger.info(f"Created {len(documents)} documents with embeddings")
        
        # Insert all documents into ChromaDB at once
        collection_name = f"{repo_id}"
        insert_result = insert_document(documents, collection_name)
        if "error" in insert_result:
            logger.error(f"Error inserting documents into ChromaDB: {insert_result['error']}")
            return {
                "status": "error",
                "message": f"Error creating embedding space: {insert_result['error']}",
                "embeddings_count": 0
            }
        
        logger.info(f"Successfully created embedding space for {repo_id} with {len(documents)} embeddings")
        return {
            "status": "success",
            "message": f"Successfully created embedding space with {len(documents)} embeddings.",
            "embeddings_count": len(documents),
            "collection_name": collection_name
        }
        
    except Exception as e:
        logger.error(f"Error in create_embedding_space endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating embedding space: {str(e)}")

@router.post("/query-commits")
async def query_commits(request: QueryCommitsRequest):
    """
    Endpoint to query commit analyses using semantic search.
    
    Parameters:
    - repository_id: ID of the repository to query
    - query: The query text to search for
    - k: Number of results to return (default: 5)
    
    Returns:
    - AI-generated response based on relevant commit analyses
    """
    try:
        logger.info(f"Received query request for repository: {request.repository_id}")
        
        # Generate embedding for the query
        query_embedding = await get_text_embedding([request.query])
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            raise HTTPException(status_code=500, detail="Failed to generate embedding for query")
        
        # Query ChromaDB for nearest neighbors
        collection_name = f"{request.repository_id}"
        neighbors_result = get_k_neighbors(
            collection_name=collection_name,
            vector=query_embedding,
            k=request.k
        )
        
        if "error" in neighbors_result:
            logger.error(f"Error querying ChromaDB: {neighbors_result['error']}")
            raise HTTPException(status_code=500, detail=f"Error querying commits: {neighbors_result['error']}")
        
        results = neighbors_result.get("results", [])
        logger.info(f"Found {len(results)} relevant commit analyses")
        # Extract subcommit IDs from results
        subcommit_ids = [int(result["id"]) for result in results]
        
        # Generate AI response based on the retrieved results
        chat_response = None
        if results:
            try:
                # Call Gemini to generate a response based on the retrieved subcommits
                chat_response: ChatResponse = await answer_user_query_with_subcommits(
                    subcommits=results,
                    user_query=request.query
                )
                logger.info("Successfully generated AI response for the query")
            except Exception as e:
                logger.error(f"Error generating AI response: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Error generating AI response: {str(e)}",
                    "subcommits_ids": subcommit_ids
                }
        
        # Return the response in the requested format
        return {
            "status": "success",
            "response": chat_response
        }
        
    except Exception as e:
        logger.error(f"Error in query_commits endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying commits: {str(e)}")
