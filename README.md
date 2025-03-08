# GitHub API

A simple FastAPI application that provides endpoints to retrieve GitHub repository information using PyGithub.

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