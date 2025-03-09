from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

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

async def api_exchange_code_for_token(request: Request):
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
    data = await request.json()
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