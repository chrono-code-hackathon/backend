# GitHub OAuth Implementation

This project implements a GitHub OAuth flow for authentication in a FastAPI application.

## How It Works

1. **Frontend OAuth Flow**:
   - User clicks "Login with GitHub" on the frontend
   - Frontend redirects to GitHub OAuth page
   - After authorization, GitHub redirects back with an authorization code
   - Frontend sends this code to the backend

2. **Backend Token Exchange**:
   - Backend exchanges the code for a GitHub access token
   - Access token is sent back to the frontend

3. **Token Storage**:
   - Frontend stores the token in localStorage
   - The token is used for subsequent API requests

4. **Protected API Requests**:
   - Frontend includes the token in the Authorization header
   - Backend uses the token to make GitHub API requests

## Setup

1. Create a `.env` file with the following variables:
   ```
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the server:
   ```
   python main.py
   ```

## CORS Configuration

The API is configured to allow cross-origin requests from any origin during development. This makes it easy to develop with a separate frontend application.

For production, you should restrict CORS to specific domains. An example of how to do this is commented in the `main.py` file.

## API Endpoints

- `POST /api/v1/auth/exchange_code`: Exchange GitHub authorization code for an access token
- Protected endpoints under `/api/v1/github/` and `/api/v1/analysis/` require a valid GitHub token

## Frontend Integration

```javascript
// Example of how to use the token in frontend requests
async function fetchUserData() {
  const token = localStorage.getItem('github_token');
  
  const response = await fetch('/api/v1/github/user', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

## Features

- Retrieve all commits from a GitHub repository
- Filter commits by branch or file path
- Simple and easy-to-use API

## Installation

1. Make sure you have Python 3.9+ installed
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Or if you're using Poetry:

```bash
poetry install
```

## Running the API

Start the API server:

```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Get Repository Commits

```
GET /github/commits
```

Query Parameters:
- `repo_url` (required): GitHub repository URL (e.g., https://github.com/owner/repo) or owner/repo format
- `branch` (optional): Branch name to filter commits
- `path` (optional): File path to filter commits

Example:

```
GET /github/commits?repo_url=microsoft/vscode&branch=main&path=src/vs/editor
```

## Authentication

By default, the API uses unauthenticated GitHub API access, which has rate limits. 
To increase rate limits, you can modify the code to use a GitHub personal access token.

## License

MIT 