"""Tests für das 4-Schichten Gedächtnis-System.

Einfache Tests ohne externe Dependencies (kein Redis, kein Chroma).
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Füge src zum Path hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from memory import (
    InMemoryBuffer,
    EpisodicMemory,
    UnifiedMemoryManager,
    LearningEpisode,
    MemoryConfig
)


def test_short_term_memory():
    """Testet Short Term Memory (InMemoryBuffer)."""
    print("\n=== Testing Short Term Memory ===")
    
    buffer = InMemoryBuffer(customer_id="test-customer")
    
    # Test set/get
    buffer.set("test_key", "test_value")
    assert buffer.get("test_key") == "test_value", "Basic get/set failed"
    print("✓ Basic get/set works")
    
    # Test TTL (kurz)
    buffer.set("ttl_key", "ttl_value", ttl=1)
    assert buffer.get("ttl_key") == "ttl_value", "TTL set failed"
    print("✓ TTL set works")
    
    # Test default
    assert buffer.get("nonexistent", "default") == "default", "Default value failed"
    print("✓ Default value works")
    
    # Test has/delete
    assert buffer.has("test_key") == True, "has() failed"
    buffer.delete("test_key")
    assert buffer.has("test_key") == False, "delete() failed"
    print("✓ has()/delete() works")
    
    # Test Reasoning Steps
    step1 = buffer.add_reasoning_step("observe", "Observing system state")
    step2 = buffer.add_reasoning_step("reason", "Reasoning about problem")
    
    steps = buffer.get_reasoning_steps()
    assert len(steps) == 2, f"Expected 2 steps, got {len(steps)}"
    assert steps[0].phase == "observe", "First step phase wrong"
    assert steps[1].phase == "reason", "Second step phase wrong"
    print("✓ Reasoning steps work")
    
    # Test ORPA state
    buffer.set_orpa_phase("plan")
    assert buffer.get_orpa_phase() == "plan", "ORPA phase failed"
    
    buffer.add_observation("Test observation")
    assert len(buffer.get_observations()) == 1, "Observation failed"
    print("✓ ORPA state works")
    
    # Test session info
    info = buffer.get_session_info()
    assert info["customer_id"] == "test-customer", "Session info customer wrong"
    assert info["reasoning_steps_count"] == 2, "Session info steps wrong"
    print("✓ Session info works")
    
    print("✅ Short Term Memory: ALL TESTS PASSED")
    return True


def test_episodic_memory():
    """Testet Episodic Memory (SQLite)."""
    print("\n=== Testing Episodic Memory ===")
    
    # Temporäre DB
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_episodic.db")
    
    try:
        memory = EpisodicMemory(
            customer_id="test-customer",
            db_path=db_path
        )
        
        # Test Ticket Resolution
        episode_id = memory.record_ticket_resolution(
            ticket_id="TICKET-001",
            problem="Checkout payment error",
            solution="Fixed validation in PaymentController",
            success=True,
            metadata={"component": "checkout"}
        )
        assert episode_id is not None, "Episode ID is None"
        print(f"✓ Recorded episode with ID: {episode_id}")
        
        # Test retrieve
        resolution = memory.get_ticket_resolution("TICKET-001")
        assert resolution is not None, "Resolution not found"
        assert resolution["ticket_id"] == "TICKET-001", "Wrong ticket ID"
        assert resolution["success"] == True, "Wrong success status"
        assert "checkout" in resolution["problem_summary"].lower(), "Wrong problem"
        print("✓ Resolution retrieval works")
        
        # Test conversation
        msg_id = memory.add_conversation_message(
            ticket_id="TICKET-001",
            role="user",
            content="I have a payment issue",
            metadata={"channel": "slack"}
        )
        assert msg_id is not None, "Message ID is None"
        print("✓ Conversation message added")
        
        history = memory.get_conversation_history("TICKET-001")
        assert len(history) == 1, f"Expected 1 message, got {len(history)}"
        assert history[0]["role"] == "user", "Wrong role"
        assert "payment" in history[0]["content"], "Wrong content"
        print("✓ Conversation history works")
        
        # Test search (keyword-based)
        # Füge weitere Episoden hinzu
        memory.record_ticket_resolution(
            ticket_id="TICKET-002",
            problem="Product import failing",
            solution="Updated CSV format",
            success=True
        )
        
        results = memory.get_relevant_episodes("payment error", n_results=3)
        assert len(results) > 0, "No search results"
        # Sollte TICKET-001 finden (enthält "payment")
        found_payment = any("payment" in r.get("problem_summary", "").lower() for r in results)
        assert found_payment, "Expected payment-related result"
        print(f"✓ Search found {len(results)} relevant episodes")
        
        # Test stats
        stats = memory.get_stats()
        assert stats["total_episodes"] == 2, f"Expected 2 episodes, got {stats['total_episodes']}"
        assert stats["successful_resolutions"] == 2, "Wrong success count"
        assert stats["total_conversation_messages"] == 1, "Wrong message count"
        print("✓ Stats work correctly")
        
        print("✅ Episodic Memory: ALL TESTS PASSED")
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_unified_memory_manager():
    """Testet UnifiedMemoryManager (ohne Redis/Chroma)."""
    print("\n=== Testing Unified Memory Manager ===")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        config = MemoryConfig(
            episodic_db_dir=temp_dir
        )
        
        manager = UnifiedMemoryManager(
            customer_id="test-customer",
            config=config,
            redis_client=None,  # Kein Redis
            chroma_client=None  # Kein Chroma
        )
        
        # Test store/retrieve (short_term)
        manager.store_context("test_key", "test_value", tier="short_term")
        result = manager.retrieve_context("test_key", tier="short_term")
        assert result == "test_value", f"Expected 'test_value', got {result}"
        print("✓ Store/retrieve short_term works")
        
        # Test auto-tier (sollte short_term wählen)
        manager.store_context("current_task", "fixing bug")
        result = manager.retrieve_context("current_task")
        assert result == "fixing bug", "Auto-tier failed"
        print("✓ Auto-tier works")
        
        # Test chat
        success = manager.add_chat_message(
            ticket_id="TICKET-001",
            role="user",
            content="Help needed"
        )
        # Ohne Redis sollte es False zurückgeben
        assert success == False, "Expected False without Redis"
        print("✓ Chat without Redis returns False (expected)")
        
        # Test learning
        episode = LearningEpisode(
            ticket_id="TICKET-001",
            problem="Payment error in checkout",
            solution="Fixed validation logic",
            success=True,
            metadata={"component": "checkout"}
        )
        
        success = manager.record_learning(episode)
        assert success == True, "record_learning failed"
        print("✓ Record learning works")
        
        # Test get relevant learnings
        learnings = manager.get_relevant_learnings("payment error", n_results=3)
        assert len(learnings) > 0, "No learnings found"
        print(f"✓ Found {len(learnings)} relevant learnings")
        
        # Test recent learnings
        recent = manager.get_recent_learnings()
        assert len(recent) == 1, f"Expected 1 recent, got {len(recent)}"
        assert recent[0]["ticket_id"] == "TICKET-001", "Wrong ticket in recent"
        print("✓ Recent learnings work")
        
        # Test build agent context
        context = manager.build_agent_context(
            ticket_id="TICKET-001",
            ticket_description="payment checkout error"
        )
        assert context["customer_id"] == "test-customer", "Wrong customer"
        assert context["ticket_id"] == "TICKET-001", "Wrong ticket"
        assert "relevant_learnings" in context, "Missing learnings"
        print("✓ Build agent context works")
        
        # Test stats
        stats = manager.get_stats()
        assert "tiers" in stats, "Missing tiers in stats"
        assert "short_term" in stats["tiers"], "Missing short_term stats"
        assert "episodic" in stats["tiers"], "Missing episodic stats"
        print("✓ Stats work")
        
        print("✅ Unified Memory Manager: ALL TESTS PASSED")
        return True
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_memory_config():
    """Testet MemoryConfig."""
    print("\n=== Testing Memory Config ===")
    
    config = MemoryConfig(
        short_term_ttl=1800,
        redis_host="redis.example.com",
        chroma_persist_dir="/data/chroma"
    )
    
    assert config.short_term_ttl == 1800, "Wrong TTL"
    assert config.redis_host == "redis.example.com", "Wrong Redis host"
    assert config.chroma_persist_dir == "/data/chroma", "Wrong Chroma dir"
    print("✓ MemoryConfig works")
    
    # Test auto-tier keywords
    assert "ticket_" in config.auto_tier_keywords, "Missing ticket_ keyword"
    assert config.auto_tier_keywords["ticket_"] == "session", "Wrong tier for ticket_"
    print("✓ Auto-tier keywords work")
    
    print("✅ Memory Config: ALL TESTS PASSED")
    return True


def run_all_tests():
    """Führt alle Tests aus."""
    print("=" * 60)
    print("4-SCHICHTEN GEDÄCHTNIS-SYSTEM TESTS")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Short Term", test_short_term_memory()))
    except Exception as e:
        print(f"❌ Short Term FAILED: {e}")
        results.append(("Short Term", False))
    
    try:
        results.append(("Episodic", test_episodic_memory()))
    except Exception as e:
        print(f"❌ Episodic FAILED: {e}")
        results.append(("Episodic", False))
    
    try:
        results.append(("Unified Manager", test_unified_memory_manager()))
    except Exception as e:
        print(f"❌ Unified Manager FAILED: {e}")
        results.append(("Unified Manager", False))
    
    try:
        results.append(("Memory Config", test_memory_config()))
    except Exception as e:
        print(f"❌ Memory Config FAILED: {e}")
        results.append(("Memory Config", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:20s} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
