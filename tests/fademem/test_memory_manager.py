"""
Unit tests for FadeMem Memory Manager
"""

import unittest
import time
from pageindex.memory_manager import MemoryEntry, MemoryManager


class TestMemoryEntry(unittest.TestCase):
    """Test MemoryEntry class"""
    
    def test_memory_entry_creation(self):
        """Test creating a memory entry"""
        entry = MemoryEntry(
            node_id="test_001",
            title="Test Entry",
            content={"summary": "Test summary", "text": "Test text"},
            importance_score=0.5,
            layer="SML"
        )
        
        self.assertEqual(entry.node_id, "test_001")
        self.assertEqual(entry.title, "Test Entry")
        self.assertEqual(entry.layer, "SML")
        self.assertEqual(entry.importance_score, 0.5)
        self.assertEqual(entry.strength, 1.0)
        self.assertEqual(entry.access_count, 0)
    
    def test_update_access(self):
        """Test access update"""
        entry = MemoryEntry("test_001", "Test", {})
        initial_access = entry.last_accessed
        initial_count = entry.access_count
        
        time.sleep(0.1)
        entry.update_access()
        
        self.assertGreater(entry.last_accessed, initial_access)
        self.assertEqual(entry.access_count, initial_count + 1)
    
    def test_recency_score(self):
        """Test recency score calculation"""
        entry = MemoryEntry("test_001", "Test", {})
        
        # Recent access should have high score
        score1 = entry.calculate_recency_score()
        self.assertGreater(score1, 0.9)
        
        # Simulate old access
        entry.last_accessed = time.time() - 86400  # 1 day ago
        score2 = entry.calculate_recency_score()
        self.assertLess(score2, score1)
    
    def test_frequency_score(self):
        """Test frequency score calculation"""
        entry = MemoryEntry("test_001", "Test", {})
        
        # No access
        score0 = entry.calculate_frequency_score()
        self.assertEqual(score0, 0.0)
        
        # Multiple accesses
        for _ in range(10):
            entry.update_access()
        
        score10 = entry.calculate_frequency_score()
        self.assertGreater(score10, score0)
    
    def test_importance_update(self):
        """Test importance score update"""
        entry = MemoryEntry("test_001", "Test", {})
        
        # Update with semantic score
        entry.update_importance_score(semantic_score=0.8)
        
        # Should have updated importance
        self.assertGreater(entry.importance_score, 0.0)
        self.assertLessEqual(entry.importance_score, 1.0)
    
    def test_decay_application(self):
        """Test exponential decay"""
        entry = MemoryEntry("test_001", "Test", {})
        initial_strength = entry.strength
        
        # Apply decay
        entry.apply_decay(time_delta=86400)  # 1 day
        
        # Strength should decrease
        self.assertLess(entry.strength, initial_strength)
        self.assertGreaterEqual(entry.strength, 0.0)
    
    def test_serialization(self):
        """Test to_dict and from_dict"""
        entry = MemoryEntry(
            node_id="test_001",
            title="Test Entry",
            content={"summary": "Test"},
            importance_score=0.7
        )
        entry.update_access()
        
        # Convert to dict
        data = entry.to_dict()
        
        # Restore from dict
        restored = MemoryEntry.from_dict(data)
        
        self.assertEqual(restored.node_id, entry.node_id)
        self.assertEqual(restored.title, entry.title)
        self.assertEqual(restored.importance_score, entry.importance_score)


class TestMemoryManager(unittest.TestCase):
    """Test MemoryManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = MemoryManager()
    
    def test_add_entry(self):
        """Test adding entries"""
        entry = self.manager.add_entry(
            node_id="test_001",
            title="Test Entry",
            content={"summary": "Test"},
            importance_score=0.5
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.layer, "SML")
        self.assertEqual(self.manager.stats['total_entries'], 1)
    
    def test_add_high_importance_entry(self):
        """Test adding high importance entry goes to LML"""
        entry = self.manager.add_entry(
            node_id="test_001",
            title="Important Entry",
            content={"summary": "Important"},
            importance_score=0.8
        )
        
        self.assertEqual(entry.layer, "LML")
        self.assertEqual(self.manager.stats['lml_entries'], 1)
    
    def test_get_entry(self):
        """Test retrieving entry"""
        self.manager.add_entry("test_001", "Test", {})
        
        entry = self.manager.get_entry("test_001")
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.access_count, 1)  # Access should be updated
    
    def test_promotion(self):
        """Test promotion from SML to LML"""
        # Add low importance entry
        self.manager.add_entry("test_001", "Test", {}, importance_score=0.5)
        
        # Update importance to high
        entry = self.manager.get_entry("test_001")
        entry.importance_score = 0.8
        
        # Check promotions
        self.manager.check_promotions_demotions()
        
        # Should be promoted to LML
        self.assertEqual(entry.layer, "LML")
        self.assertIn("test_001", self.manager.lml)
        self.assertEqual(self.manager.stats['promotions'], 1)
    
    def test_demotion(self):
        """Test demotion from LML to SML"""
        # Add high importance entry
        self.manager.add_entry("test_001", "Test", {}, importance_score=0.8)
        
        # Update importance to low
        entry = self.manager.get_entry("test_001")
        entry.importance_score = 0.2
        
        # Check demotions
        self.manager.check_promotions_demotions()
        
        # Should be demoted to SML
        self.assertEqual(entry.layer, "SML")
        self.assertIn("test_001", self.manager.sml)
        self.assertEqual(self.manager.stats['demotions'], 1)
    
    def test_prune_low_strength(self):
        """Test pruning low strength entries"""
        # Add entry and reduce strength
        self.manager.add_entry("test_001", "Test", {}, importance_score=0.3)
        entry = self.manager.get_entry("test_001")
        entry.strength = 0.05  # Below pruning threshold
        
        # Prune
        pruned = self.manager.prune_low_strength_entries()
        
        self.assertEqual(len(pruned), 1)
        self.assertNotIn("test_001", self.manager.sml)
        self.assertEqual(self.manager.stats['pruned_entries'], 1)
    
    def test_get_all_entries_sorted(self):
        """Test getting all entries sorted by importance"""
        self.manager.add_entry("test_001", "Low", {}, importance_score=0.3)
        self.manager.add_entry("test_002", "High", {}, importance_score=0.9)
        self.manager.add_entry("test_003", "Medium", {}, importance_score=0.6)
        
        entries = self.manager.get_all_entries(sort_by_importance=True)
        
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].node_id, "test_002")  # Highest importance
        self.assertEqual(entries[2].node_id, "test_001")  # Lowest importance
    
    def test_get_stats(self):
        """Test getting statistics"""
        self.manager.add_entry("test_001", "Test1", {}, importance_score=0.8)
        self.manager.add_entry("test_002", "Test2", {}, importance_score=0.4)
        
        stats = self.manager.get_stats()
        
        self.assertEqual(stats['total_entries'], 2)
        self.assertEqual(stats['lml_entries'], 1)
        self.assertEqual(stats['sml_entries'], 1)
        self.assertGreater(stats['lml_avg_importance'], stats['sml_avg_importance'])


if __name__ == '__main__':
    unittest.main()
