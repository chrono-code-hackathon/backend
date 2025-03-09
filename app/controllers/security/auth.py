from github import Github
from typing import Optional, Dict, Any
from app.config.settings import settings
    
def exchange_code_for_token(auth_code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """
    Exchange an authorization code for a GitHub access token.
    
    Args:
        auth_code: The authorization code received from GitHub OAuth flow
        redirect_uri: The redirect URI used in the initial authorization request (optional)
        
    Returns:
        Dictionary containing the access token and related information
    """
    try:
        # Initialize GitHub client
        g = Github()
        
        # Exchange the code for an access token
        token_data = g.get_oauth_application(
            client_id=settings.GITHUB_CLIENT_ID,
            client_secret=settings.GITHUB_CLIENT_SECRET
        ).get_access_token(auth_code, redirect_uri)
        
        # Return token information
        return {
            "access_token": token_data.token,
            "token_type": "bearer",
            "scope": token_data.scope,
            "expires_in": getattr(token_data, "expires_in", None)
        }
    except Exception as e:
        print(f"Error exchanging code for token: {e}")
        return {
            "error": str(e),
            "success": False
        }