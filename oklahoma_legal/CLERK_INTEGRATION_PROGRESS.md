# Clerk Authentication Integration - Progress Report

## Status: Backend Complete ✅ | Frontend Pending ⏳ | Database Migration Needed 📋

---

## What's Been Completed

### 1. Backend Configuration ✅
**File**: `config_production.py`

Added Clerk configuration:
```python
CLERK_PUBLISHABLE_KEY = 'pk_test_aHVtb3JvdXMtYmFzaWxpc2stMjIuY2xlcmsuYWNjb3VudHMuZGV2JA'
CLERK_SECRET_KEY = 'sk_test_Ug5Da7Jt8Bd6hjQZesCZC9AIcffvONL4rd538piMzN'
CLERK_FRONTEND_API = 'https://humorous-basilisk-22.clerk.accounts.dev'
```

### 2. JWT Verification Helper ✅
**File**: `auth_helpers.py`

Created complete authentication system:
- `verify_clerk_token()`: Verifies JWT tokens from Clerk
- `get_user_from_request()`: Extracts user info from requests
- `@optional_auth`: Decorator for optional authentication
- `@require_auth`: Decorator for required authentication

Features:
- Fetches and caches Clerk's JWKS (JSON Web Key Set)
- Validates JWT signatures using RS256 algorithm
- Extracts user information (user_id, email, name, etc.)
- Handles anonymous users gracefully

### 3. Python Dependencies ✅
Installed required packages:
```bash
pip install python-jose[cryptography] requests
```

Packages:
- `python-jose`: JWT verification
- `cryptography`: Cryptographic operations
- `requests`: HTTP requests for JWKS

### 4. Database Migration Script ✅
**File**: `add_user_id_to_sessions.sql`

SQL script to add user_id support:
```sql
ALTER TABLE conversation_sessions
ADD COLUMN IF NOT EXISTS user_id TEXT DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_conversation_sessions_user_id
ON conversation_sessions(user_id);
```

---

## Next Steps (In Order)

### Step 1: Apply Database Migration 📋

**Action Required**: Run `add_user_id_to_sessions.sql` in Supabase

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `add_user_id_to_sessions.sql`
4. Click "Run" to execute the migration
5. Verify the column was added (check the SELECT statement at the end)

**Expected Result**:
```
column_name    | data_type | is_nullable
---------------|-----------|------------
id             | uuid      | NO
created_at     | timestamp | YES
updated_at     | timestamp | YES
user_ip        | text      | YES
session_metadata | jsonb   | YES
user_id        | text      | YES  ← NEW COLUMN
```

###Step 2: Update ConversationManager ⏳

**File**: `conversation_manager.py`

Need to modify `create_session()` to accept and store `user_id`:

```python
def create_session(self, user_id: Optional[str] = None, user_ip: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
    """
    Create a new conversation session

    Args:
        user_id: Optional Clerk user ID for authenticated users
        user_ip: Optional user IP for tracking
        metadata: Optional metadata to store with session
    """
    try:
        session_data = {
            'user_id': user_id,  # NEW: Link session to user
            'user_ip': user_ip,
            'session_metadata': metadata or {}
        }
        # ... rest of the method
```

### Step 3: Update /ask Endpoint ⏳

**File**: `app.py`

Import auth helpers and use optional authentication:

```python
from auth_helpers import optional_auth, get_user_from_request

@app.route('/ask', methods=['POST'])
@limiter.limit("10 per minute")
@optional_auth  # NEW: Add authentication decorator
def ask(current_user=None):  # NEW: Receive current_user
    """Handle RAG question-answering requests with optional authentication"""
    try:
        # ... existing code ...

        # Extract user_id if authenticated
        user_id = current_user['user_id'] if current_user else None

        # Log authentication status
        if current_user:
            print(f"[AUTH] Request from user: {current_user['user_id']} ({current_user.get('email')})")
        else:
            print("[AUTH] Anonymous request")

        # Create session with user_id
        if not session_id:
            session_id = conversation_manager.create_session(
                user_id=user_id,  # NEW: Pass user_id
                user_ip=user_ip,
                metadata={'model': model}
            )

        # ... rest of the endpoint ...
```

### Step 4: Update Frontend with Clerk SDK ⏳

**File**: `templates/index.html`

#### 4.1 Add Clerk Script Tag

Add to `<head>` section (before closing `</head>`):

```html
<!-- Clerk JavaScript SDK -->
<script
  async
  crossorigin="anonymous"
  data-clerk-publishable-key="pk_test_aHVtb3JvdXMtYmFzaWxpc2stMjIuY2xlcmsuYWNjb3VudHMuZGV2JA"
  src="https://humorous-basilisk-22.clerk.accounts.dev/npm/@clerk/clerk-js@latest/dist/clerk.browser.js"
  onload="window.Clerk.load()"
></script>
```

#### 4.2 Add Authentication UI

Add after the header (around line 788):

```html
<!-- User Authentication Section -->
<div class="auth-section" id="authSection" style="text-align: center; margin: 20px 0;">
    <!-- Signed Out State -->
    <div id="signedOutState">
        <button class="auth-btn" onclick="showSignIn()">
            🔐 Sign In
        </button>
    </div>

    <!-- Signed In State -->
    <div id="signedInState" style="display: none;">
        <div class="user-profile">
            <img id="userAvatar" src="" alt="User" class="user-avatar">
            <span id="userName" class="user-name"></span>
            <button class="auth-btn-secondary" onclick="handleSignOut()">Sign Out</button>
        </div>
    </div>
</div>

<!-- Clerk Sign-In Component Container -->
<div id="clerkSignIn" style="display: none; max-width: 400px; margin: 20px auto;"></div>
```

#### 4.3 Add CSS Styles

Add to `<style>` section:

```css
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
    cursor: pointer;
}

.user-profile {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
}

.user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid var(--primary);
}

.user-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
}
```

#### 4.4 Add JavaScript for Clerk Integration

Add to `<script>` section (around line 917):

```javascript
// Clerk Authentication
let clerkInstance = null;
let currentUser = null;

// Initialize Clerk when page loads
window.addEventListener('load', async () => {
    try {
        // Wait for Clerk to be available
        if (window.Clerk) {
            clerkInstance = window.Clerk;

            await clerkInstance.load();

            // Check if user is signed in
            if (clerkInstance.user) {
                handleUserSignedIn(clerkInstance.user);
            } else {
                handleUserSignedOut();
            }

            // Listen for authentication state changes
            clerkInstance.addListener((resources) => {
                if (resources.user) {
                    handleUserSignedIn(resources.user);
                } else {
                    handleUserSignedOut();
                }
            });
        }
    } catch (error) {
        console.error('Failed to initialize Clerk:', error);
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
    const fullName = user.fullName || user.primaryEmailAddress?.emailAddress || 'User';
    document.getElementById('userName').textContent = fullName;
    document.getElementById('userAvatar').src = user.imageUrl || '';

    console.log('User signed in:', user.id);
}

// Handle user signed out
function handleUserSignedOut() {
    currentUser = null;

    // Update UI
    document.getElementById('signedOutState').style.display = 'block';
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

// Get authentication token for API calls
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

#### 4.5 Update API Calls to Include Auth Token

Modify `askQuestion()` function:

```javascript
async function askQuestion() {
    // ... existing code ...

    try {
        // Get auth token if user is signed in
        const authToken = await getAuthToken();

        const headers = { 'Content-Type': 'application/json' };
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const response = await fetch('/ask', {
            method: 'POST',
            headers: headers,  // Include auth header
            body: JSON.stringify(requestBody),
        });

        // ... rest of the function ...
    }
}
```

---

## Authentication Flow

### For Anonymous Users (No Change)
1. User visits site
2. Can immediately ask questions
3. Sessions created without `user_id` (remains NULL)
4. Conversations work exactly as before

### For Authenticated Users (New)
1. User visits site
2. Clicks "Sign In" button
3. Clerk shows sign-in UI (magic link or Google OAuth)
4. User signs in
5. Clerk returns JWT token
6. Frontend includes token in API requests
7. Backend verifies token and extracts `user_id`
8. Sessions linked to `user_id`
9. User can access conversations across devices

---

## Testing Checklist

Once implementation is complete:

### Anonymous User Testing
- [ ] Can ask questions without signing in
- [ ] Conversations work (session_id stored)
- [ ] "New Conversation" button works
- [ ] No authentication UI visible (or dismissible)

### Authenticated User Testing
- [ ] Can click "Sign In" button
- [ ] Clerk sign-in UI appears
- [ ] Magic link authentication works
- [ ] Google OAuth authentication works
- [ ] User profile displays after sign-in
- [ ] Auth token sent with requests
- [ ] Backend logs show "Request from user: [user_id]"
- [ ] Sessions linked to user_id in database
- [ ] Can sign out successfully

### Cross-Device Testing
- [ ] Sign in on Device A
- [ ] Ask question and note session_id
- [ ] Sign in on Device B (same account)
- [ ] Verify can access same conversations (future feature)

---

## Production Deployment

### Environment Variables for Render

Add to Render environment variables:

```
CLERK_PUBLISHABLE_KEY=pk_test_aHVtb3JvdXMtYmFzaWxpc2stMjIuY2xlcmsuYWNjb3VudHMuZGV2JA
CLERK_SECRET_KEY=sk_test_Ug5Da7Jt8Bd6hjQZesCZC9AIcffvONL4rd538piMzN
CLERK_FRONTEND_API=https://humorous-basilisk-22.clerk.accounts.dev
```

**Note**: For production, you'll want to use production keys (pk_live_... and sk_live_...)

### Update Clerk Dashboard for Production

1. Add production domain to allowed origins
2. Update redirect URLs for production
3. Switch to production keys when deploying

---

## Security Considerations

### ✅ What's Secure
- JWT tokens verified using Clerk's public keys
- Tokens expire automatically (set by Clerk)
- Secret key never exposed to frontend
- Anonymous users still supported (optional auth)
- User data isolated by user_id

### ⚠️ Future Improvements
- Add Row Level Security (RLS) policies in Supabase
- Implement rate limiting per user
- Add refresh token handling
- Monitor failed authentication attempts

---

## Next Immediate Action

**You need to**: Run the SQL migration in Supabase

1. Open Supabase dashboard
2. Go to SQL Editor
3. Run `add_user_id_to_sessions.sql`
4. Confirm the migration succeeded
5. Let me know when it's done, and I'll continue with the frontend integration

Once the migration is complete, I'll update the remaining files and we can test the authentication flow!
