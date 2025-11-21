#!/usr/bin/env python3
"""
Conversation Manager for maintaining chat context
Stores conversation history in Supabase to enable multi-turn conversations
"""

import os
from typing import List, Dict, Optional
from supabase import create_client
from datetime import datetime
import uuid

# Import configurations
if os.getenv('PRODUCTION') or os.getenv('RENDER'):
    from config_production import SUPABASE_URL, SUPABASE_KEY
else:
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
    except ImportError:
        from config_production import SUPABASE_URL, SUPABASE_KEY


class ConversationManager:
    """Manage conversation history for multi-turn dialogue"""

    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
                'user_id': user_id,
                'user_ip': user_ip,
                'session_metadata': metadata or {}
            }

            result = self.supabase.table('conversation_sessions').insert(session_data).execute()

            if result.data and len(result.data) > 0:
                session_id = result.data[0]['id']
                user_label = f"user: {user_id}" if user_id else "anonymous"
                print(f"[ConversationManager] Created new session: {session_id} ({user_label})")
                return session_id
            else:
                raise Exception("Failed to create session - no data returned")

        except Exception as e:
            print(f"[ERROR] Failed to create session: {e}")
            # Return a temporary UUID if database fails
            return str(uuid.uuid4())

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add a message to a conversation

        Args:
            session_id: Session UUID
            role: 'user', 'assistant', or 'system'
            content: Message content
            metadata: Optional metadata (e.g., sources, tokens used)

        Returns:
            True if successful, False otherwise
        """
        try:
            message_data = {
                'session_id': session_id,
                'role': role,
                'content': content,
                'metadata': metadata or {}
            }

            self.supabase.table('conversation_messages').insert(message_data).execute()

            # Update session timestamp
            self.supabase.table('conversation_sessions').update({
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', session_id).execute()

            return True

        except Exception as e:
            print(f"[ERROR] Failed to add message: {e}")
            return False

    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Get conversation history for a session

        Args:
            session_id: Session UUID
            limit: Maximum number of messages to retrieve (default: 10)

        Returns:
            List of messages in chronological order
        """
        try:
            result = self.supabase.table('conversation_messages')\
                .select('role, content, created_at, metadata')\
                .eq('session_id', session_id)\
                .order('created_at', desc=False)\
                .limit(limit)\
                .execute()

            if result.data:
                return result.data
            return []

        except Exception as e:
            print(f"[ERROR] Failed to get conversation history: {e}")
            return []

    def get_messages_for_llm(self, session_id: str, max_messages: int = 10) -> List[Dict]:
        """
        Get conversation history formatted for OpenAI API

        Args:
            session_id: Session UUID
            max_messages: Maximum number of messages to include

        Returns:
            List of messages in OpenAI format: [{"role": "user", "content": "..."}, ...]
        """
        history = self.get_conversation_history(session_id, limit=max_messages)

        # Format for OpenAI API
        messages = []
        for msg in history:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        return messages

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        try:
            result = self.supabase.table('conversation_sessions')\
                .select('id')\
                .eq('id', session_id)\
                .limit(1)\
                .execute()

            return result.data and len(result.data) > 0

        except Exception as e:
            print(f"[ERROR] Failed to check session existence: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session and all its messages"""
        try:
            # Messages will be cascade deleted due to foreign key
            self.supabase.table('conversation_sessions')\
                .delete()\
                .eq('id', session_id)\
                .execute()

            print(f"[ConversationManager] Deleted session: {session_id}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to delete session: {e}")
            return False

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session metadata"""
        try:
            result = self.supabase.table('conversation_sessions')\
                .select('*')\
                .eq('id', session_id)\
                .limit(1)\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None

        except Exception as e:
            print(f"[ERROR] Failed to get session info: {e}")
            return None


def test_conversation_manager():
    """Test the conversation manager"""
    manager = ConversationManager()

    print("=" * 60)
    print("Testing Conversation Manager")
    print("=" * 60)

    # Create a new session
    print("\n1. Creating new session...")
    session_id = manager.create_session(user_ip="127.0.0.1", metadata={"test": True})
    print(f"   Session ID: {session_id}")

    # Add some messages
    print("\n2. Adding messages...")
    manager.add_message(session_id, "user", "What are voting rights in Oklahoma?")
    manager.add_message(session_id, "assistant", "According to Oklahoma Constitution Article III...",
                       metadata={"tokens": 150, "sources": 3})
    manager.add_message(session_id, "user", "Can you tell me more about that?")

    # Retrieve history
    print("\n3. Retrieving conversation history...")
    history = manager.get_conversation_history(session_id)
    print(f"   Found {len(history)} messages:")
    for msg in history:
        print(f"   - [{msg['role']}] {msg['content'][:50]}...")

    # Get formatted for LLM
    print("\n4. Getting messages formatted for LLM...")
    llm_messages = manager.get_messages_for_llm(session_id)
    print(f"   Formatted {len(llm_messages)} messages for OpenAI API")

    # Check session info
    print("\n5. Getting session info...")
    info = manager.get_session_info(session_id)
    if info:
        print(f"   Created: {info['created_at']}")
        print(f"   Updated: {info['updated_at']}")

    # Clean up
    print("\n6. Cleaning up test session...")
    manager.delete_session(session_id)
    print("   Session deleted")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_conversation_manager()
