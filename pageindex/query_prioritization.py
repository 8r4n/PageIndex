"""
Enhanced Query Prioritization Module for FadeMem-PageIndex

This module implements importance-based retrieval prioritization for queries,
considering recent query patterns, decay values, and semantic relevance.
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from .utils import ChatGPT_API_async, extract_json
from .memory_manager import MemoryEntry
import time


class QueryPrioritization:
    """
    Handles importance-based prioritization of memory retrieval
    """
    
    def __init__(self, model: str = "gpt-4o-2024-11-20"):
        """
        Initialize query prioritization module
        
        Args:
            model: LLM model to use for semantic relevance calculation
        """
        self.model = model
        self.query_history = []  # Track recent queries
        self.max_history = 100  # Keep last 100 queries
    
    def add_query_to_history(self, query: str):
        """Add a query to the history"""
        self.query_history.append({
            'query': query,
            'timestamp': time.time()
        })
        # Keep only recent queries
        if len(self.query_history) > self.max_history:
            self.query_history = self.query_history[-self.max_history:]
    
    async def calculate_semantic_relevance(self, query: str, entry: MemoryEntry) -> float:
        """
        Calculate semantic relevance between query and memory entry
        
        Args:
            query: User query
            entry: Memory entry
            
        Returns:
            Relevance score between 0 and 1
        """
        content = f"Title: {entry.title}\nSummary: {entry.content.get('summary', 'N/A')}"
        
        prompt = f"""You are an expert at assessing the relevance of document sections to user queries.

User Query: {query}

Document Section:
{content}

Rate the semantic relevance of this document section to the user's query.

Return a JSON object:
{{
    "relevance_score": <float between 0 and 1, where 1 is highly relevant and 0 is not relevant>,
    "reasoning": <brief explanation of the relevance assessment>
}}

Directly return the JSON structure. Do not output anything else."""

        response = await ChatGPT_API_async(model=self.model, prompt=prompt)
        result = extract_json(response)
        
        return result.get('relevance_score', 0.0)
    
    def calculate_query_pattern_score(self, query: str, entry: MemoryEntry) -> float:
        """
        Calculate score based on recent query patterns
        
        Args:
            query: Current query
            entry: Memory entry
            
        Returns:
            Pattern score between 0 and 1
        """
        if not self.query_history:
            return 0.5  # Neutral score if no history
        
        # Check if this entry was recently relevant to similar queries
        # This is a simplified version - in production, you'd want more sophisticated pattern matching
        recent_queries = [q['query'].lower() for q in self.query_history[-10:]]
        query_lower = query.lower()
        
        # Simple keyword overlap scoring
        query_words = set(query_lower.split())
        title_words = set(entry.title.lower().split())
        
        # Count how many recent queries had similar keywords
        similar_count = 0
        for recent_q in recent_queries:
            recent_words = set(recent_q.split())
            if len(query_words & recent_words) > 0:
                similar_count += 1
        
        # Normalize by history size
        pattern_score = min(1.0, similar_count / len(recent_queries) if recent_queries else 0.5)
        
        return pattern_score
    
    def calculate_composite_score(self, entry: MemoryEntry, semantic_relevance: float, 
                                  query_pattern_score: float) -> float:
        """
        Calculate composite retrieval score combining multiple factors
        
        Args:
            entry: Memory entry
            semantic_relevance: Semantic relevance to query
            query_pattern_score: Score based on query patterns
            
        Returns:
            Composite score between 0 and 1
        """
        # Weight factors:
        # - 50% semantic relevance (most important)
        # - 20% importance score (from memory manager)
        # - 15% strength (decay-adjusted)
        # - 10% query pattern
        # - 5% recency
        
        recency = entry.calculate_recency_score()
        
        composite = (
            0.50 * semantic_relevance +
            0.20 * entry.importance_score +
            0.15 * entry.strength +
            0.10 * query_pattern_score +
            0.05 * recency
        )
        
        return composite
    
    async def prioritize_entries(self, query: str, entries: List[MemoryEntry], 
                                top_k: Optional[int] = None) -> List[Tuple[MemoryEntry, float]]:
        """
        Prioritize and rank memory entries for a given query
        
        Args:
            query: User query
            entries: List of memory entries to prioritize
            top_k: Number of top results to return (None for all)
            
        Returns:
            List of tuples (entry, score) sorted by priority score descending
        """
        # Add query to history
        self.add_query_to_history(query)
        
        # Calculate semantic relevance for all entries in parallel
        tasks = [self.calculate_semantic_relevance(query, entry) for entry in entries]
        semantic_scores = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate composite scores
        ranked_entries = []
        for entry, semantic_score in zip(entries, semantic_scores):
            if isinstance(semantic_score, Exception):
                semantic_score = 0.0
            
            # Update entry's semantic relevance scores
            entry.update_importance_score(semantic_score)
            
            # Calculate query pattern score
            pattern_score = self.calculate_query_pattern_score(query, entry)
            
            # Calculate composite score
            composite_score = self.calculate_composite_score(entry, semantic_score, pattern_score)
            
            ranked_entries.append((entry, composite_score))
        
        # Sort by composite score descending
        ranked_entries.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k if specified
        if top_k is not None:
            ranked_entries = ranked_entries[:top_k]
        
        return ranked_entries
    
    async def retrieve_with_prioritization(self, query: str, entries: List[MemoryEntry],
                                          top_k: int = 5, layer_preference: Optional[str] = None) -> Dict:
        """
        Retrieve and prioritize entries with optional layer preference
        
        Args:
            query: User query
            entries: List of memory entries
            top_k: Number of top results to return
            layer_preference: Optional preference for "LML" or "SML" (adds boost to scores)
            
        Returns:
            Dictionary with retrieval results
        """
        # Prioritize entries
        ranked_entries = await self.prioritize_entries(query, entries, top_k=None)
        
        # Apply layer preference if specified
        if layer_preference in ["LML", "SML"]:
            layer_boost = 0.1
            for i, (entry, score) in enumerate(ranked_entries):
                if entry.layer == layer_preference:
                    # Boost score for preferred layer
                    ranked_entries[i] = (entry, min(1.0, score + layer_boost))
            
            # Re-sort after applying boost
            ranked_entries.sort(key=lambda x: x[1], reverse=True)
        
        # Get top_k
        top_entries = ranked_entries[:top_k]
        
        return {
            'query': query,
            'total_entries': len(entries),
            'top_k': top_k,
            'results': [
                {
                    'node_id': entry.node_id,
                    'title': entry.title,
                    'layer': entry.layer,
                    'score': score,
                    'importance_score': entry.importance_score,
                    'strength': entry.strength,
                    'summary': entry.content.get('summary', 'N/A')
                }
                for entry, score in top_entries
            ],
            'layer_distribution': {
                'LML': sum(1 for e, _ in top_entries if e.layer == "LML"),
                'SML': sum(1 for e, _ in top_entries if e.layer == "SML")
            }
        }
