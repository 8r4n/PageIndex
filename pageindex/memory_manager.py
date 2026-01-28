"""
FadeMem-inspired Memory Management Module for PageIndex

This module implements biologically-inspired memory management features including:
- Dual-layer memory architecture (Long-term Memory Layer and Short-term Memory Layer)
- Adaptive forgetting mechanism with exponential decay
- Dynamic importance scoring
- Memory promotion/demotion thresholds
"""

import time
import math
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import copy


class MemoryEntry:
    """Represents a single memory entry in the PageIndex system"""
    
    def __init__(self, node_id: str, title: str, content: dict, 
                 importance_score: float = 0.5, layer: str = "SML"):
        """
        Initialize a memory entry
        
        Args:
            node_id: Unique identifier for the node
            title: Title of the memory entry
            content: Full node content (including summary, text, etc.)
            importance_score: Initial importance score (0-1)
            layer: Memory layer ("LML" or "SML")
        """
        self.node_id = node_id
        self.title = title
        self.content = content
        self.importance_score = importance_score
        self.layer = layer
        
        # Temporal tracking
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
        
        # Decay parameters
        self.decay_rate = 0.1  # Will be adjusted based on importance
        self.strength = 1.0  # Current memory strength
        
        # Semantic relevance tracking
        self.semantic_relevance_scores = []
        
    def update_access(self):
        """Update access statistics"""
        self.last_accessed = time.time()
        self.access_count += 1
        
    def calculate_recency_score(self) -> float:
        """Calculate recency score based on time since last access"""
        time_since_access = time.time() - self.last_accessed
        # Exponential decay: score decreases as time increases
        # Using 1 day (86400 seconds) as the half-life
        half_life = 86400
        recency_score = math.exp(-time_since_access / half_life)
        return recency_score
    
    def calculate_frequency_score(self) -> float:
        """Calculate frequency score based on access count"""
        # Logarithmic scaling to prevent over-weighting highly accessed items
        if self.access_count == 0:
            return 0.0
        # Normalize to 0-1 range using log scale
        frequency_score = min(1.0, math.log(self.access_count + 1) / 10)
        return frequency_score
    
    def update_importance_score(self, semantic_score: Optional[float] = None):
        """
        Update importance score based on recency, frequency, and semantic relevance
        
        Args:
            semantic_score: Optional semantic relevance score to include
        """
        recency = self.calculate_recency_score()
        frequency = self.calculate_frequency_score()
        
        # Track semantic scores if provided
        if semantic_score is not None:
            self.semantic_relevance_scores.append(semantic_score)
            # Use average of recent semantic scores (last 5)
            recent_semantic = self.semantic_relevance_scores[-5:]
            avg_semantic = sum(recent_semantic) / len(recent_semantic)
        else:
            avg_semantic = 0.5  # Neutral default
        
        # Weighted combination: 30% recency, 30% frequency, 40% semantic
        self.importance_score = (0.3 * recency + 0.3 * frequency + 0.4 * avg_semantic)
        
        # Update decay rate based on importance
        # Higher importance = lower decay rate
        self.decay_rate = 0.5 * (1 - self.importance_score)
    
    def apply_decay(self, time_delta: Optional[float] = None):
        """
        Apply exponential decay to memory strength
        
        Args:
            time_delta: Time elapsed since last decay (in seconds)
                       If None, calculates from last_accessed
        """
        if time_delta is None:
            time_delta = time.time() - self.last_accessed
        
        # Exponential decay formula: S(t) = S(0) * e^(-λt)
        # where λ is the decay rate
        self.strength *= math.exp(-self.decay_rate * time_delta / 86400)  # Normalize by day
        
        # Ensure strength stays within bounds
        self.strength = max(0.0, min(1.0, self.strength))
    
    def to_dict(self) -> dict:
        """Convert memory entry to dictionary for serialization"""
        return {
            'node_id': self.node_id,
            'title': self.title,
            'content': self.content,
            'importance_score': self.importance_score,
            'layer': self.layer,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'decay_rate': self.decay_rate,
            'strength': self.strength,
            'semantic_relevance_scores': self.semantic_relevance_scores[-5:]  # Keep recent 5
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MemoryEntry':
        """Create memory entry from dictionary"""
        entry = cls(
            node_id=data['node_id'],
            title=data['title'],
            content=data['content'],
            importance_score=data.get('importance_score', 0.5),
            layer=data.get('layer', 'SML')
        )
        entry.created_at = data.get('created_at', time.time())
        entry.last_accessed = data.get('last_accessed', time.time())
        entry.access_count = data.get('access_count', 0)
        entry.decay_rate = data.get('decay_rate', 0.1)
        entry.strength = data.get('strength', 1.0)
        entry.semantic_relevance_scores = data.get('semantic_relevance_scores', [])
        return entry


class MemoryManager:
    """
    Manages dual-layer memory architecture with adaptive forgetting
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize memory manager
        
        Args:
            config: Configuration dictionary with parameters:
                - lml_threshold: Importance score threshold for LML promotion (default: 0.7)
                - sml_threshold: Importance score threshold for SML demotion (default: 0.3)
                - pruning_threshold: Strength threshold for pruning (default: 0.1)
                - dormancy_threshold: Days of inactivity before considering dormant (default: 30)
        """
        self.config = config or {}
        
        # Thresholds
        self.lml_threshold = self.config.get('lml_threshold', 0.7)
        self.sml_threshold = self.config.get('sml_threshold', 0.3)
        self.pruning_threshold = self.config.get('pruning_threshold', 0.1)
        self.dormancy_threshold = self.config.get('dormancy_threshold', 30 * 86400)  # 30 days in seconds
        
        # Memory layers
        self.lml: Dict[str, MemoryEntry] = {}  # Long-term Memory Layer
        self.sml: Dict[str, MemoryEntry] = {}  # Short-term Memory Layer
        
        # Statistics
        self.stats = {
            'total_entries': 0,
            'lml_entries': 0,
            'sml_entries': 0,
            'promotions': 0,
            'demotions': 0,
            'pruned_entries': 0
        }
    
    def add_entry(self, node_id: str, title: str, content: dict, 
                  importance_score: Optional[float] = None) -> MemoryEntry:
        """
        Add a new memory entry
        
        Args:
            node_id: Unique identifier for the node
            title: Title of the memory entry
            content: Full node content
            importance_score: Optional initial importance score
            
        Returns:
            Created memory entry
        """
        # Determine initial layer based on importance
        if importance_score is None:
            importance_score = 0.5
            layer = "SML"
        elif importance_score >= self.lml_threshold:
            layer = "LML"
        else:
            layer = "SML"
        
        entry = MemoryEntry(node_id, title, content, importance_score, layer)
        
        if layer == "LML":
            self.lml[node_id] = entry
            self.stats['lml_entries'] += 1
        else:
            self.sml[node_id] = entry
            self.stats['sml_entries'] += 1
        
        self.stats['total_entries'] += 1
        return entry
    
    def get_entry(self, node_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry and update its access statistics"""
        entry = self.lml.get(node_id) or self.sml.get(node_id)
        if entry:
            entry.update_access()
        return entry
    
    def update_entry_importance(self, node_id: str, semantic_score: Optional[float] = None):
        """Update importance score for an entry"""
        entry = self.get_entry(node_id)
        if entry:
            entry.update_importance_score(semantic_score)
    
    def apply_decay_to_all(self):
        """Apply decay to all memory entries"""
        for entry in list(self.lml.values()) + list(self.sml.values()):
            entry.apply_decay()
    
    def check_promotions_demotions(self):
        """
        Check and perform promotions from SML to LML and demotions from LML to SML
        """
        # Check SML for promotions
        to_promote = []
        for node_id, entry in self.sml.items():
            if entry.importance_score >= self.lml_threshold:
                to_promote.append(node_id)
        
        for node_id in to_promote:
            entry = self.sml.pop(node_id)
            entry.layer = "LML"
            self.lml[node_id] = entry
            self.stats['promotions'] += 1
            self.stats['sml_entries'] -= 1
            self.stats['lml_entries'] += 1
        
        # Check LML for demotions
        to_demote = []
        for node_id, entry in self.lml.items():
            if entry.importance_score < self.sml_threshold:
                to_demote.append(node_id)
        
        for node_id in to_demote:
            entry = self.lml.pop(node_id)
            entry.layer = "SML"
            self.sml[node_id] = entry
            self.stats['demotions'] += 1
            self.stats['lml_entries'] -= 1
            self.stats['sml_entries'] += 1
    
    def prune_low_strength_entries(self) -> List[str]:
        """
        Remove entries with strength below pruning threshold
        
        Returns:
            List of pruned node IDs
        """
        pruned = []
        
        # Check SML for low strength entries
        for node_id, entry in list(self.sml.items()):
            if entry.strength < self.pruning_threshold:
                del self.sml[node_id]
                pruned.append(node_id)
                self.stats['pruned_entries'] += 1
                self.stats['sml_entries'] -= 1
                self.stats['total_entries'] -= 1
        
        # LML entries are more protected, only prune if very weak
        very_low_threshold = self.pruning_threshold / 2
        for node_id, entry in list(self.lml.items()):
            if entry.strength < very_low_threshold:
                del self.lml[node_id]
                pruned.append(node_id)
                self.stats['pruned_entries'] += 1
                self.stats['lml_entries'] -= 1
                self.stats['total_entries'] -= 1
        
        return pruned
    
    def prune_dormant_entries(self) -> List[str]:
        """
        Remove entries that have been dormant for too long
        
        Returns:
            List of pruned node IDs
        """
        pruned = []
        current_time = time.time()
        
        # Only prune dormant entries from SML
        for node_id, entry in list(self.sml.items()):
            time_inactive = current_time - entry.last_accessed
            if time_inactive > self.dormancy_threshold:
                del self.sml[node_id]
                pruned.append(node_id)
                self.stats['pruned_entries'] += 1
                self.stats['sml_entries'] -= 1
                self.stats['total_entries'] -= 1
        
        return pruned
    
    def get_all_entries(self, sort_by_importance: bool = True) -> List[MemoryEntry]:
        """
        Get all memory entries
        
        Args:
            sort_by_importance: If True, sort by importance score descending
            
        Returns:
            List of all memory entries
        """
        all_entries = list(self.lml.values()) + list(self.sml.values())
        
        if sort_by_importance:
            all_entries.sort(key=lambda x: x.importance_score, reverse=True)
        
        return all_entries
    
    def get_entries_by_layer(self, layer: str) -> List[MemoryEntry]:
        """Get all entries from a specific layer"""
        if layer == "LML":
            return list(self.lml.values())
        elif layer == "SML":
            return list(self.sml.values())
        else:
            return []
    
    def get_stats(self) -> Dict:
        """Get current memory statistics"""
        stats = copy.deepcopy(self.stats)
        stats['lml_avg_importance'] = (
            sum(e.importance_score for e in self.lml.values()) / len(self.lml)
            if self.lml else 0
        )
        stats['sml_avg_importance'] = (
            sum(e.importance_score for e in self.sml.values()) / len(self.sml)
            if self.sml else 0
        )
        stats['lml_avg_strength'] = (
            sum(e.strength for e in self.lml.values()) / len(self.lml)
            if self.lml else 0
        )
        stats['sml_avg_strength'] = (
            sum(e.strength for e in self.sml.values()) / len(self.sml)
            if self.sml else 0
        )
        return stats
    
    def save_to_file(self, filepath: str):
        """Save memory state to JSON file"""
        state = {
            'config': self.config,
            'stats': self.stats,
            'lml': {k: v.to_dict() for k, v in self.lml.items()},
            'sml': {k: v.to_dict() for k, v in self.sml.items()}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load memory state from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        self.config = state.get('config', {})
        self.stats = state.get('stats', {})
        
        self.lml = {k: MemoryEntry.from_dict(v) for k, v in state.get('lml', {}).items()}
        self.sml = {k: MemoryEntry.from_dict(v) for k, v in state.get('sml', {}).items()}
        
        # Update thresholds from loaded config
        self.lml_threshold = self.config.get('lml_threshold', 0.7)
        self.sml_threshold = self.config.get('sml_threshold', 0.3)
        self.pruning_threshold = self.config.get('pruning_threshold', 0.1)
        self.dormancy_threshold = self.config.get('dormancy_threshold', 30 * 86400)
