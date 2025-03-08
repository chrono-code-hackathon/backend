# Mock commits for testing
from datetime import datetime

from app.models.models_commit import Commit, File


mock_commits = [
    Commit(
        created_at="2023-05-15T10:30:00Z",
        repo_name="project-alpha",
        sha="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
        author="Alice Johnson",
        date="2023-05-15T10:30:00Z",
        message="Refactor authentication module to enhance security and improve user experience",
        url="https://github.com/org/project-alpha/commit/a1b2c3d4e5",
        author_email="alice@example.com",
        description="""This commit addresses several critical issues within the authentication module.
        - Implements multi-factor authentication (MFA) using TOTP for enhanced security.
        - Introduces rate limiting to prevent brute-force attacks on login endpoints.
        - Refactors password hashing to use Argon2 for improved resistance against rainbow table attacks.
        - Updates session management to use HTTPOnly and Secure flags to mitigate XSS and session hijacking vulnerabilities.
        - Adds detailed logging for authentication events, including successful logins, failed logins, and MFA attempts, to aid in security monitoring and incident response.
        - Implements a password reset flow with email verification to allow users to securely recover their accounts.
        - Improves error handling and provides more informative error messages to users during the login process.
        - Updates dependencies to the latest versions to address known security vulnerabilities.
        """,
        author_url="https://github.com/alicejohnson",
        files=[
            File(
                filename="auth/login.py",
                additions=150,
                deletions=75,
                changes=225,
                status="modified",
                raw_url="https://github.com/org/project-alpha/raw/a1b2c3d4e5/auth/login.py",
                blob_url="https://github.com/org/project-alpha/blob/a1b2c3d4e5/auth/login.py",
                patch="""@@ -42,7 +42,15 @@ def validate_user(username, password):
        # Existing code...
        +    # Implement rate limiting to prevent brute-force attacks
        +    if rate_limit_exceeded(username):
        +        return False, "Too many login attempts. Please try again later."
        +
        +    # Verify MFA if enabled
        +    if user.mfa_enabled:
        +        if not verify_totp(username, totp_code):
        +            return False, "Invalid MFA code."
        +
        # More new code...
        """
            ),
            File(
                filename="auth/mfa.py",
                additions=80,
                deletions=0,
                changes=80,
                status="added",
                raw_url="https://github.com/org/project-alpha/raw/a1b2c3d4e5/auth/mfa.py",
                blob_url="https://github.com/org/project-alpha/blob/a1b2c3d4e5/auth/mfa.py",
                patch="""@@ -0,0 +1,80 @@
        +# MFA implementation using TOTP
        +import pyotp
        +
        +def generate_totp_secret():
        +    # Generates a new TOTP secret key
        +    return pyotp.random_base32()
        +
        +def get_totp_uri(secret, username):
        +    # Generates a TOTP URI for use with authenticator apps
        +    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="Project Alpha")
        +
        +def verify_totp(secret, code):
        +    # Verifies a TOTP code against the secret key
        +    totp = pyotp.TOTP(secret)
        +    return totp.verify(code)
        """
            ),
            File(
                filename="requirements.txt",
                additions=2,
                deletions=0,
                changes=2,
                status="modified",
                raw_url="https://github.com/org/project-alpha/raw/a1b2c3d4e5/requirements.txt",
                blob_url="https://github.com/org/project-alpha/blob/a1b2c3d4e5/requirements.txt",
                patch="""@@ -10,0 +11,2 @@
        +pyotp
        +argon2-cffi
        """
            )
        ]
    ),
    Commit(
        created_at="2023-06-02T14:45:00Z",
        repo_name="project-beta",
        sha="b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1",
        author="Bob Smith",
        date="2023-06-02T14:45:00Z",
        message="Implement comprehensive dark mode support with accessibility enhancements and user customization options",
        url="https://github.com/org/project-beta/commit/b2c3d4e5f6",
        author_email="bob@example.com",
        description="""This commit introduces a complete dark mode implementation across the entire application, focusing on accessibility and user customization.
        - Implements a new CSS theme using semantic variables for colors, fonts, and spacing, ensuring consistency and maintainability.
        - Adds a ThemeProvider component using React Context to manage the application's theme state and provide it to all components.
        - Creates a ThemeToggle component that allows users to switch between light and dark modes with a smooth transition effect.
        - Implements user preference persistence using local storage to remember the user's preferred theme across sessions.
        - Enhances accessibility by ensuring sufficient contrast ratios between text and background colors in both light and dark modes, meeting WCAG AA guidelines.
        - Provides user customization options, allowing users to adjust the color palette and font sizes within the selected theme.
        - Adds unit tests to verify the correct rendering of components in both light and dark modes.
        - Updates documentation to explain how to use the new theme and customization options.
        """,
        author_url="https://github.com/bobsmith",
        files=[
            File(
                filename="styles/theme.css",
                additions=780,
                deletions=120,
                changes=900,
                status="modified",
                raw_url="https://github.com/org/project-beta/raw/b2c3d4e5f6/styles/theme.css",
                blob_url="https://github.com/org/project-beta/blob/b2c3d4e5f6/styles/theme.css",
                patch="""@@ -105,12 +105,78 @@ .light-theme {
        +    --primary-color: #007bff;
        +    --secondary-color: #6c757d;
        +    --background-color: #f8f9fa;
        +    --text-color: #212529;
        +}
        +
        +.dark-theme {
        +    --primary-color: #66b3ff;
        +    --secondary-color: #adb5bd;
        +    --background-color: #343a40;
        +    --text-color: #f8f9fa;
        +}
        """
            ),
            File(
                filename="components/ThemeToggle.js",
                additions=450,
                deletions=0,
                changes=450,
                status="added",
                raw_url="https://github.com/org/project-beta/raw/b2c3d4e5f6/components/ThemeToggle.js",
                blob_url="https://github.com/org/project-beta/blob/b2c3d4e5f6/components/ThemeToggle.js",
                patch="""@@ -0,0 +1,45 @@ import React from 'react';
        +import { ThemeContext } from './ThemeContext';
        +
        +const ThemeToggle = () => {
        +    const { theme, toggleTheme } = React.useContext(ThemeContext);
        +
        +    return (
        +        <button onClick={toggleTheme}>
        +            {theme === 'light' ? 'Enable Dark Mode' : 'Enable Light Mode'}
        +        </button>
        +    );
        +};
        +
        +export default ThemeToggle;
        """
            ),
            File(
                filename="components/ThemeContext.js",
                additions=100,
                deletions=0,
                changes=100,
                status="added",
                raw_url="https://github.com/org/project-beta/raw/b2c3d4e5f6/components/ThemeContext.js",
                blob_url="https://github.com/org/project-beta/blob/b2c3d4e5f6/components/ThemeContext.js",
                patch="""@@ -0,0 +1,100 @@
        +import React, { useState, createContext } from 'react';
        +
        +export const ThemeContext = createContext();
        +
        +export const ThemeProvider = ({ children }) => {
        +    const [theme, setTheme] = useState('light');
        +
        +    const toggleTheme = () => {
        +        setTheme(prevTheme => (prevTheme === 'light' ? 'dark' : 'light'));
        +    };
        +
        +    return (
        +        <ThemeContext.Provider value={{ theme, toggleTheme }}>
        +            {children}
        +        </ThemeContext.Provider>
        +    );
        +};
        """
            )
        ]
    ),
    Commit(
        created_at="2023-07-10T09:15:00Z",
        repo_name="project-gamma",
        sha="c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2",
        author="Carol Davis",
        date="2023-07-10T09:15:00Z",
        message="Optimize database queries and implement caching strategies for significant performance improvements and reduced database load",
        url="https://github.com/org/project-gamma/commit/c3d4e5f6g7",
        author_email="carol@example.com",
        description="""This commit focuses on optimizing database queries and implementing caching strategies to improve application performance and reduce database load.
        - Implements query optimization techniques, including indexing, query rewriting, and the use of stored procedures, resulting in a 60% reduction in query execution time.
        - Introduces a multi-layered caching strategy using Redis for frequently accessed data, including user profiles, product catalogs, and search results.
        - Implements cache invalidation policies to ensure data consistency and prevent stale data from being served.
        - Adds monitoring and logging to track cache hit rates, cache eviction rates, and query execution times, allowing for continuous performance optimization.
        - Refactors database connection pooling to reduce the overhead of establishing new connections.
        - Implements asynchronous query execution to prevent blocking the main thread and improve responsiveness.
        - Adds unit tests to verify the correctness of the caching implementation and the optimized queries.
        """,
        author_url="https://github.com/caroldavis",
        files=[
            File(
                filename="database/queries.py",
                additions=320,
                deletions=280,
                changes=600,
                status="modified",
                raw_url="https://github.com/org/project-gamma/raw/c3d4e5f6g7/database/queries.py",
                blob_url="https://github.com/org/project-gamma/blob/c3d4e5f6g7/database/queries.py",
                patch="""@@ -78,28 +78,32 @@ def get_user_data(user_id):
        +    # Use Redis cache to retrieve user data
        +    user_data = redis_client.get(f"user:{user_id}")
        +    if user_data:
        +        return json.loads(user_data)
        +
        +    # Execute the database query if data is not in cache
        +    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        +    user_data = cursor.fetchone()
        +
        +    # Store the data in Redis cache
        +    redis_client.set(f"user:{user_id}", json.dumps(user_data), ex=3600)
        +
        +    return user_data
        """
            ),
            File(
                filename="database/schema.sql",
                additions=50,
                deletions=0,
                changes=50,
                status="modified",
                raw_url="https://github.com/org/project-gamma/raw/c3d4e5f6g7/database/schema.sql",
                blob_url="https://github.com/org/project-gamma/blob/c3d4e5f6g7/database/schema.sql",
                patch="""@@ -120,0 +121,5 @@ CREATE TABLE users (
        +CREATE INDEX idx_users_email ON users (email);
        +CREATE INDEX idx_users_username ON users (username);
        """
            ),
            File(
                filename="cache/redis_client.py",
                additions=100,
                deletions=0,
                changes=100,
                status="added",
                raw_url="https://github.com/org/project-gamma/raw/c3d4e5f6g7/cache/redis_client.py",
                blob_url="https://github.com/org/project-gamma/blob/c3d4e5f6g7/cache/redis_client.py",
                patch="""@@ -0,0 +1,100 @@
        +import redis
        +
        +class RedisClient:
        +    def __init__(self, host='localhost', port=6379, db=0):
        +        self.redis = redis.Redis(host=host, port=port, db=db)
        +
        +    def get(self, key):
        +        try:
        +            return self.redis.get(key)
        +        except redis.exceptions.ConnectionError as e:
        +            print(f"Error connecting to Redis: {e}")
        +            return None
        +
        +    def set(self, key, value, ex=None):
        +        try:
        +            self.redis.set(key, value, ex=ex)
        +        except redis.exceptions.ConnectionError as e:
        +            print(f"Error connecting to Redis: {e}")
        +
        +redis_client = RedisClient()
        """
            )
        ]
    ),
    Commit(
        created_at="2023-08-22T16:00:00Z",
        repo_name="project-delta",
        sha="d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3",
        author="Dave Wilson",
        date="2023-08-22T16:00:00Z",
        message="Implement robust security measures to protect against API vulnerabilities, including input validation, authentication enhancements, and rate limiting",
        url="https://github.com/org/project-delta/commit/d4e5f6g7h8",
        author_email="dave@example.com",
        description="""This commit addresses critical security vulnerabilities in the API endpoints and implements robust security measures to protect against unauthorized access and data breaches.
        - Implements comprehensive input validation using JSON schema validation to prevent injection attacks and ensure data integrity.
        - Enhances authentication by implementing JWT (JSON Web Token) based authentication with refresh tokens for improved security and scalability.
        - Introduces rate limiting to prevent denial-of-service (DoS) attacks and protect against abuse of API endpoints.
        - Implements proper authorization checks to ensure that users only have access to the resources they are authorized to access.
        - Adds detailed logging and monitoring to detect and respond to security incidents in a timely manner.
        - Updates dependencies to the latest versions to address known security vulnerabilities.
        - Implements security headers to protect against common web attacks, such as XSS and clickjacking.
        """,
        author_url="https://github.com/davewilson",
        files=[
            File(
                filename="api/endpoints.py",
                additions=80,
                deletions=30,
                changes=110,
                status="modified",
                raw_url="https://github.com/org/project-delta/raw/d4e5f6g7h8/api/endpoints.py",
                blob_url="https://github.com/org/project-delta/blob/d4e5f6g7h8/api/endpoints.py",
                patch="""@@ -203,7 +203,12 @@ def get_user_data():
        +    # Validate input using JSON schema
        +    validate_input(request.json, user_data_schema)
        +
        +    # Authenticate user using JWT
        +    user = authenticate_user(request.headers.get('Authorization'))
        """
            ),
            File(
                filename="middleware/auth.py",
                additions=170,
                deletions=50,
                changes=220,
                status="modified",
                raw_url="https://github.com/org/project-delta/raw/d4e5f6g7h8/middleware/auth.py",
                blob_url="https://github.com/org/project-delta/blob/d4e5f6g7h8/middleware/auth.py",
                patch="""@@ -45,9 +45,21 @@ def validate_token(token):
        +    # Verify JWT token
        +    try:
        +        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        +        return payload['user_id']
        +    except jwt.ExpiredSignatureError:
        +        return None
        +    except jwt.InvalidTokenError:
        +        return None
        """
            ),
            File(
                filename="config/security.py",
                additions=50,
                deletions=0,
                changes=50,
                status="added",
                raw_url="https://github.com/org/project-delta/raw/d4e5f6g7h8/config/security.py",
                blob_url="https://github.com/org/project-delta/blob/d4e5f6g7h8/config/security.py",
                patch="""@@ -0,0 +1,50 @@
        +# Security configuration settings
        +import os
        +
        +SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
        +ALGORITHM = 'HS256'
        +ACCESS_TOKEN_EXPIRE_MINUTES = 30
        """
            )
        ]
    ),
    Commit(
        created_at="2023-09-05T11:20:00Z",
        repo_name="project-epsilon",
        sha="e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4",
        author="Eve Brown",
        date="2023-09-05T11:20:00Z",
        message="Implement comprehensive unit and integration tests for the payment processing module, including edge cases and error handling scenarios",
        url="https://github.com/org/project-epsilon/commit/e5f6g7h8i9",
        author_email="eve@example.com",
        description="""This commit adds comprehensive unit and integration tests for the payment processing module to ensure reliability, prevent regression issues, and cover various edge cases and error handling scenarios.
        - Implements unit tests for individual functions and classes within the payment processing module, covering different input values and expected outputs.
        - Adds integration tests to verify the interaction between different components of the payment processing module, including the payment gateway, the transaction database, and the notification system.
        - Covers edge cases, such as invalid card numbers, insufficient funds, and expired cards, to ensure that the system handles these scenarios gracefully.
        - Implements tests for error handling scenarios, such as network failures, database connection errors, and payment gateway timeouts, to ensure that the system recovers properly from these errors.
        - Adds test coverage reports to track the percentage of code covered by tests and identify areas that need additional testing.
        - Implements continuous integration (CI) to automatically run tests whenever code is committed to the repository.
        """,
        author_url="https://github.com/evebrown",
        files=[
            File(
                filename="tests/test_payment.py",
                additions=1200,
                deletions=0,
                changes=1200,
                status="added",
                raw_url="https://github.com/org/project-epsilon/raw/e5f6g7h8i9/tests/test_payment.py",
                blob_url="https://github.com/org/project-epsilon/blob/e5f6g7h8i9/tests/test_payment.py",
                patch="""@@ -0,0 +1,120 @@ import unittest
        +from payment.processor import process_payment
        +
        +class TestPaymentProcessing(unittest.TestCase):
        +    def test_successful_payment(self):
        +        # Test a successful payment
        +        result = process_payment(100, 'valid_card_details')
        +        self.assertTrue(result['success'])
        +        self.assertEqual(result['amount'], 100)
        +
        +    def test_invalid_card_number(self):
        +        # Test with an invalid card number
        +        result = process_payment(100, 'invalid_card_number')
        +        self.assertFalse(result['success'])
        +        self.assertEqual(result['error'], 'Invalid card number')
        """
            ),
            File(
                filename="payment/processor.py",
                additions=50,
                deletions=20,
                changes=70,
                status="modified",
                raw_url="https://github.com/org/project-epsilon/raw/e5f6g7h8i9/payment/processor.py",
                blob_url="https://github.com/org/project-epsilon/blob/e5f6g7h8i9/payment/processor.py",
                patch="""@@ -87,7 +87,10 @@ def process_payment(amount, card_details):
        +    # Validate card details
        +    if not validate_card(card_details):
        +        return {'success': False, 'error': 'Invalid card details'}
        """
            ),
            File(
                filename=".github/workflows/ci.yml",
                additions=60,
                deletions=0,
                changes=60,
                status="added",
                raw_url="https://github.com/org/project-epsilon/raw/e5f6g7h8i9/.github/workflows/ci.yml",
                blob_url="https://github.com/org/project-epsilon/blob/e5f6g7h8i9/.github/workflows/ci.yml",
                patch="""@@ -0,0 +1,60 @@
        +name: CI
        +
        +on:
        +  push:
        +    branches: [ "main" ]
        +  pull_request:
        +    branches: [ "main" ]
        +
        +jobs:
        +  build:
        +    runs-on: ubuntu-latest
        +
        +    steps:
        +      - uses: actions/checkout@v3
        +      - name: Set up Python 3.10
        +        uses: actions/setup-python@v3
        +        with:
        +          python-version: "3.10"
        +      - name: Install dependencies
        +        run: |
        +          python -m pip install --upgrade pip
        +          pip install -r requirements.txt
        +      - name: Run tests
        +        run: |
        +          python -m unittest discover -s tests
        """
            )
        ]
    )
]