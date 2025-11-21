# Clerk Authentication Implementation Plan

## Overview
Integrate Clerk authentication into the Oklahoma Legal Research application with optional authentication, magic link, and Google OAuth support.

## Frontend Architecture Analysis
- **Framework**: Plain HTML/JavaScript (not React)
- **Current structure**: Single-page app with inline JavaScript in `templates/index.html`
- **Session tracking**: Uses localStorage for simple session IDs (line 1145-1152)
- **API calls**: Fetch API to `/ask`, `/search`, `/feedback`, `/general-feedback`

## Implementation Steps

### 1. Set Up Clerk Application

**Action Items:**
1. Go to [clerk.com](https://clerk.com) and create account
2. Create a new application called "Oklahoma Legal Research"
3. Enable authentication methods:
   - ✅ Email (Magic Link) - passwordless authentication
   - ✅ Google OAuth - social sign-in
   - ❌ Disable password-based authentication (unless user wants it)
4. Get API keys:
   - **Publishable Key** (starts with `pk_test_` or `pk_live_`)
   - **Secret Key** (starts with `sk_test_` or `sk_live_`)

### 2. Frontend Integration (templates/index.html)

#### 2.1 Add Clerk JavaScript SDK

Add to `<head>` section (before closing `</head>` tag):

```html
<!-- Clerk JavaScript SDK -->
<script
  src="https://challenges.cloudflare.com/turnstile/v0/api.js"
  async
  defer
></script>
<script
  async
  crossorigin="anonymous"
  data-clerk-publishable-key="YOUR_PUBLISHABLE_KEY_HERE"
  src="https://[your-clerk-frontend-api].clerk.accounts.dev/npm/@clerk/clerk-js@latest/dist/clerk.browser.js"
  type="text/javascript"
></script>
```

Note: Replace `YOUR_PUBLISHABLE_KEY_HERE` with actual publishable key from Clerk dashboard.

#### 2.2 Add User Authentication UI

Add after the header section (around line 788, after the subtitle):

```html
<!-- User Authentication Section -->
<div class="auth-section" id="authSection">
    <!-- Signed Out State -->
    <div id="signedOutState" style="display: flex; justify-content: center; gap: 12px; margin: 20px 0;">
        <button class="auth-btn" onclick="showSignIn()">
            <span class="auth-icon">🔐</span> Sign In
        </button>
    </div>

    <!-- Signed In State -->
    <div id="signedInState" style="display: none; text-align: center; margin: 20px 0;">
        <div class="user-profile">
            <img id="userAvatar" src="" alt="User" class="user-avatar" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 12px;">
            <span id="userName" class="user-name"></span>
            <button class="auth-btn-secondary" onclick="handleSignOut()" style="margin-left: 12px;">Sign Out</button>
        </div>
    </div>
</div>

<!-- Clerk UI Components Container -->
<div id="clerkSignIn" style="display: none; max-width: 400px; margin: 20px auto;"></div>
```

#### 2.3 Add CSS Styles for Auth UI

Add to the `<style>` section (around line 777):

```css
/* Authentication Styles */
.auth-section {
    margin: 20px 0;
}

.auth-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 24px;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.auth-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

.auth-btn-secondary {
    padding: 8px 16px;
    background: var(--background);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.auth-btn-secondary:hover {
    border-color: var(--primary);
    background: var(--surface-light);
}

.user-profile {
    display: inline-flex;
    align-items: center;
    padding: 12px 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
}

.user-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
}

.user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid var(--primary);
}
```

#### 2.4 Update JavaScript for Clerk Integration

Add to the `<script>` section (around line 1290, before closing script tag):

```javascript
// Clerk Authentication Integration
let clerkInstance = null;
let currentUser = null;

// Initialize Clerk
window.addEventListener('load', async () => {
    try {
        // Initialize Clerk instance
        clerkInstance = window.Clerk;

        await clerkInstance.load({
            // Optional: Configure sign-in appearance
            appearance: {
                baseTheme: 'dark',
                variables: {
                    colorPrimary: '#6366f1'
                }
            }
        });

        // Check if user is signed in
        if (clerkInstance.user) {
            handleUserSignedIn(clerkInstance.user);
        } else {
            handleUserSignedOut();
        }

        // Listen for authentication state changes
        clerkInstance.addListener((event) => {
            if (event.user) {
                handleUserSignedIn(event.user);
            } else {
                handleUserSignedOut();
            }
        });

    } catch (error) {
        console.error('Failed to initialize Clerk:', error);
        // Continue without authentication - optional auth
        handleUserSignedOut();
    }
});

// Show sign-in UI
async function showSignIn() {
    try {
        const signInDiv = document.getElementById('clerkSignIn');
        signInDiv.style.display = 'block';

        // Mount Clerk sign-in component
        clerkInstance.mountSignIn(signInDiv, {
            routing: 'virtual',
            redirectUrl: window.location.href,
            appearance: {
                baseTheme: 'dark',
                variables: {
                    colorPrimary: '#6366f1'
                }
            }
        });
    } catch (error) {
        console.error('Failed to show sign-in:', error);
    }
}

// Handle user signed in
function handleUserSignedIn(user) {
    currentUser = user;

    // Update UI
    document.getElementById('signedOutState').style.display = 'none';
    document.getElementById('signedInState').style.display = 'block';
    document.getElementById('clerkSignIn').style.display = 'none';

    // Update user info
    document.getElementById('userName').textContent = user.fullName || user.primaryEmailAddress?.emailAddress || 'User';
    document.getElementById('userAvatar').src = user.imageUrl || '';

    console.log('User signed in:', user.id);
}

// Handle user signed out
function handleUserSignedOut() {
    currentUser = null;

    // Update UI
    document.getElementById('signedOutState').style.display = 'flex';
    document.getElementById('signedInState').style.display = 'none';
    document.getElementById('clerkSignIn').style.display = 'none';

    console.log('User signed out');
}

// Sign out handler
async function handleSignOut() {
    try {
        await clerkInstance.signOut();
        handleUserSignedOut();
    } catch (error) {
        console.error('Failed to sign out:', error);
    }
}

// Get Clerk session token for API calls
async function getAuthToken() {
    if (!clerkInstance || !clerkInstance.session) {
        return null; // No authentication - anonymous user
    }

    try {
        return await clerkInstance.session.getToken();
    } catch (error) {
        console.error('Failed to get auth token:', error);
        return null;
    }
}
```

#### 2.5 Update API Calls to Include Auth Token

Modify the `askQuestion()` function (around line 999):

```javascript
async function askQuestion() {
    const question = document.getElementById('questionInput').value.trim();
    const model = document.getElementById('modelSelect').value;

    if (!question) {
        showError('Please enter a question');
        return;
    }

    showLoading('Thinking...');

    try {
        // Get auth token if user is signed in
        const authToken = await getAuthToken();

        const headers = { 'Content-Type': 'application/json' };
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const response = await fetch('/ask', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                question: question,
                model: model,
                num_sources: 3
            }),
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.error || 'Failed to get answer');

        displayAnswer(data);

    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}
```

Apply similar changes to `performSearch()`, `submitFeedback()`, and `submitGeneralFeedback()`.

### 3. Backend Integration (app.py)

#### 3.1 Install Required Python Packages

```bash
pip install pyjwt cryptography requests
```

#### 3.2 Add Clerk Configuration

Add to `config_production.py` and `config.py`:

```python
# Clerk Authentication
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY', '')
CLERK_PUBLISHABLE_KEY = os.getenv('CLERK_PUBLISHABLE_KEY', '')
CLERK_JWKS_URL = "https://api.clerk.com/v1/jwks"  # Update with your Clerk instance URL
```

Set environment variables:
```bash
export CLERK_SECRET_KEY="sk_test_..."
export CLERK_PUBLISHABLE_KEY="pk_test_..."
```

#### 3.3 Create JWT Verification Helper

Create new file `auth_helpers.py`:

```python
#!/usr/bin/env python3
"""
Authentication helpers for verifying Clerk JWT tokens
"""

import os
import jwt
import requests
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict

# Import configurations
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import CLERK_SECRET_KEY, CLERK_JWKS_URL
else:
    try:
        from config import CLERK_SECRET_KEY, CLERK_JWKS_URL
    except ImportError:
        from config_production import CLERK_SECRET_KEY, CLERK_JWKS_URL


def get_clerk_public_key():
    """Fetch Clerk's public key for JWT verification"""
    try:
        response = requests.get(CLERK_JWKS_URL)
        jwks = response.json()
        # Get the first key (you may need to match by 'kid' in production)
        return jwks['keys'][0]
    except Exception as e:
        print(f"[ERROR] Failed to fetch Clerk public key: {e}")
        return None


def verify_clerk_token(token: str) -> Optional[Dict]:
    """
    Verify a Clerk JWT token and return the decoded payload

    Args:
        token: JWT token from Authorization header

    Returns:
        Decoded token payload if valid, None otherwise
    """
    if not token:
        return None

    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        # Get public key from Clerk
        public_key = get_clerk_public_key()
        if not public_key:
            print("[ERROR] Could not get Clerk public key")
            return None

        # Verify and decode the JWT
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            options={"verify_exp": True}
        )

        return decoded

    except jwt.ExpiredSignatureError:
        print("[ERROR] Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[ERROR] Invalid token: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Token verification failed: {e}")
        return None


def get_user_from_request() -> Optional[Dict]:
    """
    Extract and verify user from Authorization header

    Returns:
        User info dict if authenticated, None if anonymous
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return None  # Anonymous user - this is OK

    token_payload = verify_clerk_token(auth_header)

    if not token_payload:
        return None  # Invalid token - treat as anonymous

    return {
        'user_id': token_payload.get('sub'),  # Clerk user ID
        'email': token_payload.get('email'),
        'email_verified': token_payload.get('email_verified', False)
    }


def optional_auth(f):
    """
    Decorator for routes that support optional authentication
    Adds 'current_user' to kwargs (None if anonymous)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_user_from_request()
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated_function


def require_auth(f):
    """
    Decorator for routes that require authentication
    Returns 401 if not authenticated
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_user_from_request()

        if not user:
            return jsonify({'error': 'Authentication required'}), 401

        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated_function
```

#### 3.4 Update Database Schema

Add `user_id` column to `conversation_sessions` table:

```sql
-- Update conversation_sessions to support user authentication
ALTER TABLE conversation_sessions
ADD COLUMN user_id TEXT DEFAULT NULL;

-- Add index for fast user lookups
CREATE INDEX idx_conversation_sessions_user_id ON conversation_sessions(user_id);

-- Update RLS policy to allow users to see only their own conversations
-- (Optional - can implement later for tighter security)
DROP POLICY IF EXISTS "Allow all access to conversation_sessions" ON conversation_sessions;

CREATE POLICY "Users can access own sessions or anonymous sessions"
ON conversation_sessions
FOR ALL
USING (user_id IS NULL OR user_id = current_setting('request.user_id', true));
```

#### 3.5 Update Flask Routes to Use Authentication

Modify `/ask` endpoint in `app.py`:

```python
from auth_helpers import optional_auth, get_user_from_request

@app.route('/ask', methods=['POST'])
@optional_auth
def ask_question(current_user=None):
    """
    Handle natural language questions using RAG
    Supports optional authentication
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        model = data.get('model', 'gpt-4')
        num_sources = data.get('num_sources', 3)
        session_id = data.get('session_id')  # Optional session ID for conversation history

        if not question:
            return jsonify({'error': 'Question is required'}), 400

        # Log authentication status
        if current_user:
            print(f"[AUTH] Request from user: {current_user['user_id']}")
        else:
            print("[AUTH] Anonymous request")

        # TODO: If session_id provided, retrieve conversation history
        # and include in the RAG query

        # Get answer from RAG system
        result = rag.ask_question(question, num_sources=num_sources, model=model)

        if 'error' in result:
            return jsonify(result), 500

        # TODO: Store conversation in database if session exists
        # Link to user_id if authenticated

        # Return the answer
        return jsonify({
            'question': question,
            'answer': result['answer'],
            'sources': result['sources'],
            'model': model,
            'tokens_used': result['tokens_used']
        })

    except Exception as e:
        print(f"[ERROR] /ask endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
```

### 4. Update ConversationManager to Support User IDs

Modify `conversation_manager.py`:

```python
def create_session(self, user_id: Optional[str] = None, user_ip: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
    """
    Create a new conversation session

    Args:
        user_id: Optional Clerk user ID for authenticated users
        user_ip: Optional user IP for tracking
        metadata: Optional metadata to store with session

    Returns:
        session_id (UUID string)
    """
    try:
        session_data = {
            'user_id': user_id,  # NEW: Link session to user
            'user_ip': user_ip,
            'session_metadata': metadata or {}
        }

        result = self.supabase.table('conversation_sessions').insert(session_data).execute()

        if result.data and len(result.data) > 0:
            session_id = result.data[0]['id']
            print(f"[ConversationManager] Created new session: {session_id} (user: {user_id or 'anonymous'})")
            return session_id
        else:
            raise Exception("Failed to create session - no data returned")

    except Exception as e:
        print(f"[ERROR] Failed to create session: {e}")
        # Return a temporary UUID if database fails
        return str(uuid.uuid4())
```

### 5. Environment Variables Setup

Create `.env` file or add to Render environment:

```bash
# Clerk Authentication
CLERK_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
CLERK_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
CLERK_JWKS_URL=https://YOUR_CLERK_INSTANCE.clerk.accounts.dev/.well-known/jwks.json
```

### 6. Testing Checklist

- [ ] Anonymous users can use the app without signing in
- [ ] Sign-in button shows Clerk authentication UI
- [ ] Magic link authentication works
- [ ] Google OAuth authentication works
- [ ] User profile displays after sign-in
- [ ] Sign-out button works
- [ ] Auth token is sent with API requests when signed in
- [ ] Backend correctly identifies authenticated vs anonymous users
- [ ] Conversations are linked to user_id for authenticated users
- [ ] Conversations work for anonymous users (user_id = NULL)

## Benefits of This Implementation

1. **Optional Authentication**: Users can use the app anonymously or sign in
2. **Easy Sign-In**: Magic link (passwordless) and Google OAuth for convenience
3. **Better UX for Returning Users**: Authenticated users can access their conversation history across devices
4. **Privacy**: Each user's conversations are isolated
5. **Analytics**: Can track usage per user without compromising privacy
6. **Rate Limiting**: Can implement per-user rate limits to prevent abuse
7. **Future Features**: Enables saved searches, favorites, user preferences

## Production Considerations

1. **HTTPS Required**: Clerk requires HTTPS in production (Render provides this automatically)
2. **CORS**: May need to configure CORS if frontend is on different domain
3. **Rate Limiting**: Implement rate limiting per user to prevent abuse
4. **Database RLS**: Tighten Row Level Security policies to ensure users only see their data
5. **Session Management**: Add session expiration and cleanup
6. **Error Handling**: Improve error messages for authentication failures
7. **Analytics**: Track authentication usage and conversion rates

## Next Steps After Implementation

1. Add conversation history UI to show past conversations
2. Implement "Resume Conversation" feature
3. Add user preferences (preferred AI model, etc.)
4. Add saved searches or favorites
5. Implement user feedback analytics dashboard
6. Add email notifications for important updates (opt-in)
