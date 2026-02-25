"""Tests for History Manager."""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from bridge.history_manager import (
    HistoryManager, ConversationTurn, ConversationSession,
    get_history_manager
)
from bridge.session_manager import Session


class TestConversationTurn:
    """Test ConversationTurn dataclass."""
    
    def test_creation(self):
        """Test basic creation."""
        turn = ConversationTurn(
            id=1,
            session_id=2,
            turn_index=0,
            role="user",
            content="Hello"
        )
        
        assert turn.id == 1
        assert turn.session_id == 2
        assert turn.turn_index == 0
        assert turn.role == "user"
        assert turn.content == "Hello"
        
    def test_from_db_row(self):
        """Test from database row."""
        row = Mock()
        row.__getitem__ = Mock(side_effect=lambda k: {
            'id': 1,
            'session_id': 2,
            'turn_index': 3,
            'timestamp': '2024-01-01T00:00:00',
            'role': 'assistant',
            'content': 'Response',
            'message_type': 'final',
            'speakability': 'speak',
            'tool_calls': json.dumps({"tool": "test"})
        }.get(k))
        
        turn = ConversationTurn.from_db_row(row)
        
        assert turn.id == 1
        assert turn.session_id == 2
        assert turn.turn_index == 3
        assert turn.role == "assistant"
        assert turn.tool_calls == {"tool": "test"}
        
    def test_to_dict(self):
        """Test conversion to dict."""
        turn = ConversationTurn(
            id=1,
            session_id=2,
            turn_index=0,
            timestamp="2024-01-01T00:00:00",
            role="user",
            content="Hello",
            message_type="final",
            speakability="speak"
        )
        
        data = turn.to_dict()
        
        assert data['id'] == 1
        assert data['session_id'] == 2
        assert data['content'] == "Hello"


class TestConversationSession:
    """Test ConversationSession dataclass."""
    
    def test_creation(self):
        """Test basic creation."""
        session = ConversationSession(
            session_uuid="test-uuid",
            created_at="2024-01-01T00:00:00",
            state="active"
        )
        
        assert session.session_uuid == "test-uuid"
        assert session.state == "active"
        assert session.turns == []
        
    def test_to_dict(self):
        """Test serialization."""
        turn = ConversationTurn(
            id=1,
            session_id=2,
            turn_index=0,
            role="user",
            content="Hello"
        )
        
        session = ConversationSession(
            session_uuid="test",
            created_at="2024-01-01T00:00:00",
            state="closed",
            turns=[turn],
            metadata={"key": "value"}
        )
        
        data = session.to_dict()
        
        assert data['session_uuid'] == "test"
        assert len(data['turns']) == 1
        assert data['metadata'] == {"key": "value"}


class TestHistoryManager:
    """Test HistoryManager operations."""
    
    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager."""
        with patch('bridge.history_manager.get_session_manager') as mock:
            manager = Mock()
            mock.return_value = manager
            yield manager
    
    @pytest.fixture
    def mock_store(self):
        """Mock conversation store."""
        with patch('bridge.history_manager.get_conversation_store') as mock:
            store = Mock()
            mock.return_value = store
            yield store

    def _create_mock_conn(self, fetchall_result=None, fetchone_result=None, rowcount=1):
        """Helper to create properly configured mock connection."""
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = fetchall_result or []
        mock_cursor.fetchone.return_value = fetchone_result
        mock_cursor.rowcount = rowcount
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        return mock_conn
    
    def test_add_turn(self, mock_session_manager):
        """Test adding conversation turn."""
        manager = HistoryManager()
        
        # Mock the database operation
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_conn.execute.return_value = mock_cursor
        
        with patch.object(manager.store, '_get_connection', return_value=mock_conn):
            with patch.object(manager, 'get_turn') as mock_get:
                mock_get.return_value = ConversationTurn(
                    id=1, session_id=1, turn_index=0, role="user", content="Hello"
                )
                
                turn = manager.add_turn(
                    session_id=1,
                    role="user",
                    content="Hello",
                    turn_index=0
                )
                
                assert turn is not None

    def test_get_turn(self, mock_session_manager):
        """Test retrieving turn by ID."""
        manager = HistoryManager()
        
        mock_row = Mock()
        mock_row.__getitem__ = lambda self, k: {
            'id': 1, 'session_id': 2, 'turn_index': 0,
            'timestamp': '2024-01-01T00:00:00',
            'role': 'user', 'content': 'Hello',
            'message_type': None, 'speakability': None, 'tool_calls': None
        }.get(k, None)
        
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.execute.return_value = mock_cursor
        
        with patch.object(manager.store, '_get_connection', return_value=mock_conn):
            turn = manager.get_turn(1)
            
            assert turn is not None
            assert turn.id == 1
            
    def test_get_turn_not_found(self, mock_session_manager):
        """Test retrieving non-existent turn."""
        manager = HistoryManager()
        
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.execute.return_value = mock_cursor
        
        with patch.object(manager.store, '_get_connection', return_value=mock_conn):
            turn = manager.get_turn(999)
            
            assert turn is None
            
    def test_get_session_turns(self, mock_session_manager):
        """Test retrieving turns for session."""
        manager = HistoryManager()
        
        # Mock session
        mock_session = Session(session_uuid="test-uuid", id=1)
        mock_session_manager.get_session.return_value = mock_session
        
        # Mock rows
        mock_rows = [
            {'id': 1, 'session_id': 1, 'turn_index': 0, 'timestamp': '2024-01-01T00:00:00',
             'role': 'user', 'content': 'Hello', 'message_type': None, 
             'speakability': None, 'tool_calls': None},
            {'id': 2, 'session_id': 1, 'turn_index': 1, 'timestamp': '2024-01-01T00:00:01',
             'role': 'assistant', 'content': 'Hi', 'message_type': None,
             'speakability': None, 'tool_calls': None}
        ]
        
        mock_conn = self._create_mock_conn(fetchall_result=mock_rows)
        
        with patch.object(manager.store, '_get_connection', return_value=mock_conn):
            turns = manager.get_session_turns("test-uuid")
            
            assert len(turns) == 2
            assert turns[0].role == "user"
            assert turns[1].role == "assistant"
            
    def test_get_recent_turns(self, mock_session_manager):
        """Test getting recent turns."""
        manager = HistoryManager()
        
        with patch.object(manager, 'get_session_turns') as mock_get:
            mock_turns = [
                ConversationTurn(id=i, session_id=1, turn_index=i, role="user", content="Test")
                for i in range(5)
            ]
            mock_get.return_value = mock_turns
            
            turns = manager.get_recent_turns("test-uuid", count=3)
            
            mock_get.assert_called_once_with("test-uuid", 0, 3)
            
    def test_search_conversations(self, mock_session_manager):
        """Test searching conversations."""
        manager = HistoryManager()
        
        mock_rows = [
            {'id': 1, 'session_uuid': 'uuid1', 'turn_index': 0,
             'timestamp': '2024-01-01T00:00:00', 'role': 'user',
             'content': 'Hello world', 'created_at': '2024-01-01T00:00:00',
             'state': 'active'}
        ]
        
        mock_conn = self._create_mock_conn(fetchall_result=mock_rows)
        
        with patch.object(manager.store, '_get_connection', return_value=mock_conn):
            results = manager.search_conversations("world")
            
            assert len(results) == 1
            assert "world" in results[0]['content'].lower()
            
    def test_search_with_dates(self, mock_session_manager):
        """Test search with date filters."""
        manager = HistoryManager()
        
        mock_conn = MagicMock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor
        
        with patch.object(manager.store, '_get_connection', return_value=mock_conn):
            results = manager.search_conversations(
                "test",
                start_date="2024-01-01T00:00:00",
                end_date="2024-01-31T23:59:59"
            )
            
            # Search should return empty list (no errors)
            assert results == []
            # Execute was called
            assert mock_conn.execute.called
            
            
    def test_get_conversation_stats(self, mock_session_manager):
        """Test getting conversation stats."""
        manager = HistoryManager()
        
        # Use helper to create proper mock
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            [5],  # Total turns
            [0]   # Pending tools
        ]
        mock_cursor.fetchall.return_value = [
            ('user', 3), ('assistant', 2)
        ]
        
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        
        with patch.object(manager.store, '_get_connection', return_value=mock_conn):
            stats = manager.get_conversation_stats("test-uuid")
            
            assert stats['session_uuid'] == "test-uuid"
            assert stats['total_turns'] == 5
            
    def test_export_session_json(self, mock_session_manager, tmp_path):
        """Test JSON export."""
        manager = HistoryManager()
        manager.store = Mock()
        
        # Mock session
        mock_session = Session(session_uuid="test-uuid", id=1, created_at="2024-01-01T00:00:00")
        mock_session_manager.get_session.return_value = mock_session
        
        # Mock turns
        with patch.object(manager, 'get_session_turns') as mock_get_turns:
            mock_get_turns.return_value = [
                ConversationTurn(id=1, session_id=1, turn_index=0, role="user", content="Hello")
            ]
            
            output_path = tmp_path / "test.json"
            result = manager.export_session_json("test-uuid", output_path)
            
            assert result is True
            assert output_path.exists()
            
            # Verify content
            with open(output_path) as f:
                data = json.load(f)
                assert data['session_uuid'] == "test-uuid"
                
    def test_export_session_json_session_not_found(self, mock_session_manager, tmp_path):
        """Test JSON export with missing session."""
        manager = HistoryManager()
        mock_session_manager.get_session.return_value = None
        
        output_path = tmp_path / "test.json"
        result = manager.export_session_json("test-uuid", output_path)
        
        assert result is False
        
    def test_export_session_csv(self, mock_session_manager, tmp_path):
        """Test CSV export."""
        manager = HistoryManager()
        
        with patch.object(manager, 'get_session_turns') as mock_get_turns:
            mock_get_turns.return_value = [
                ConversationTurn(
                    id=1, session_id=1, turn_index=0,
                    timestamp="2024-01-01T00:00:00",
                    role="user", content="Hello",
                    message_type="final", speakability="speak"
                )
            ]
            
            output_path = tmp_path / "test.csv"
            result = manager.export_session_csv("test-uuid", output_path)
            
            assert result is True
            assert output_path.exists()
            
            # Verify content
            with open(output_path) as f:
                content = f.read()
                assert "turn_index" in content
                assert "user" in content
                
    def test_export_session_csv_no_turns(self, mock_session_manager, tmp_path):
        """Test CSV export with no turns."""
        manager = HistoryManager()
        
        with patch.object(manager, 'get_session_turns') as mock_get_turns:
            mock_get_turns.return_value = []
            
            output_path = tmp_path / "test.csv"
            result = manager.export_session_csv("test-uuid", output_path)
            
            assert result is False
            
    def test_delete_turns_for_session(self, mock_session_manager):
        """Test deleting all turns for session."""
        manager = HistoryManager()
        
        # Use helper to create proper mock
        mock_cursor = Mock()
        mock_cursor.rowcount = 5
        
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        
        with patch.object(manager.store, '_get_connection', return_value=mock_conn):
            count = manager.delete_turns_for_session("test-uuid")
            
            assert count == 5
            
    def test_get_session_turns_session_not_found(self, mock_session_manager):
        """Test getting turns when session doesn't exist."""
        manager = HistoryManager()
        mock_session_manager.get_session.return_value = None
        
        turns = manager.get_session_turns("non-existent")
        
        assert turns == []


class TestGlobalManager:
    """Test global history manager."""
    
    def test_get_history_manager_singleton(self):
        """Test global manager is singleton."""
        manager1 = get_history_manager()
        manager2 = get_history_manager()
        
        assert manager1 is manager2
