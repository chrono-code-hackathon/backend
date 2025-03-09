from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

# Import access functions
from app.security.auth import exchange_code_for_token

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# OAuth token response model
class OAuthTokenResponse(BaseModel):
    """
    OAuth Token Response Model
    
    Represents the response from GitHub's OAuth token endpoint
    """
    access_token: str = "gho_16C7e42F292c6912E7710c838347Ae178B4a"
    token_type: str = "bearer"
    scope: Optional[str] = "repo,user"
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "gho_16C7e42F292c6912E7710c838347Ae178B4a",
                "token_type": "bearer",
                "scope": "repo,user"
            }
        }

# Handle OPTIONS preflight request
@auth_router.options("/exchange_code")
async def options_exchange_code(response: Response):
    """
    Handle OPTIONS preflight request for the exchange_code endpoint.
    This is needed for CORS to work properly with some browsers.
    """
    # Manually add CORS headers to ensure they're present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return {}

@auth_router.post(
    "/exchange_code", 
    response_model=OAuthTokenResponse,
    summary="Exchange GitHub OAuth code for access token",
    responses={
        200: {
            "description": "Successfully exchanged code for token",
            "model": OAuthTokenResponse
        },
        400: {
            "description": "Bad request - Missing code or invalid code"
        },
        500: {
            "description": "Internal server error during token exchange"
        }
    }
)
async def api_exchange_code_for_token(request: Request, response: Response):
    """
    # Exchange GitHub OAuth Code for Access Token
    
    This endpoint takes a GitHub OAuth authorization code and exchanges it for an access token.
    The frontend application typically redirects to this endpoint after receiving the code from GitHub's OAuth flow.
    
    ## Request Body
    
    JSON object containing:
    - `code`: The authorization code received from GitHub OAuth flow
    
    ## Response
    
    JSON object containing:
    - `access_token`: GitHub access token to use for API requests
    - `token_type`: Token type (usually "bearer")
    - `scope`: OAuth scopes granted (comma-separated string)
    
    ## Status Codes
    
    - 200: Successfully exchanged code for token
    - 400: Bad request (missing or invalid code)
    - 500: Internal server error
    
    ## Example
    
    Request:    ```json
    {
        "code": "a1b2c3d4e5f6g7h8i9j0"
    }    ```
    
    Response:    ```json
    {
        "access_token": "gho_16C7e42F292c6912E7710c838347Ae178B4a",
        "token_type": "bearer", 
        "scope": "repo,user"
    }    ```
    """
    # Manually add CORS headers to ensure they're present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
        
    code = data.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    
    try:
        token_data = exchange_code_for_token(code)
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error"])
        
        return OAuthTokenResponse(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            scope=token_data.get("scope", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")