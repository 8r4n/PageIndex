"""
Conflict Resolution Module for FadeMem-PageIndex

This module implements LLM-guided conflict detection and resolution for memory entries,
including semantic similarity detection and intelligent conflict resolution strategies.
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from .utils import ChatGPT_API_async, extract_json
from .memory_manager import MemoryEntry


class ConflictResolver:
    """
    Handles detection and resolution of conflicts among memory entries
    """
    
    def __init__(self, model: str = "gpt-4o-2024-11-20", similarity_threshold: float = 0.8):
        """
        Initialize conflict resolver
        
        Args:
            model: LLM model to use for conflict resolution
            similarity_threshold: Threshold for considering entries as conflicting (0-1)
        """
        self.model = model
        self.similarity_threshold = similarity_threshold
        
    async def calculate_semantic_similarity(self, entry1: MemoryEntry, entry2: MemoryEntry) -> float:
        """
        Calculate semantic similarity between two memory entries using LLM
        
        Args:
            entry1: First memory entry
            entry2: Second memory entry
            
        Returns:
            Similarity score between 0 and 1
        """
        # Prepare content summaries
        content1 = f"Title: {entry1.title}\nSummary: {entry1.content.get('summary', 'N/A')}"
        content2 = f"Title: {entry2.title}\nSummary: {entry2.content.get('summary', 'N/A')}"
        
        prompt = f"""You are an expert at analyzing semantic similarity between document sections.

Compare these two memory entries and determine their semantic similarity.

Entry 1:
{content1}

Entry 2:
{content2}

Return a JSON object with:
{{
    "similarity_score": <float between 0 and 1, where 1 is identical and 0 is completely unrelated>,
    "reasoning": <brief explanation of the similarity assessment>
}}

Directly return the JSON structure. Do not output anything else."""

        response = await ChatGPT_API_async(model=self.model, prompt=prompt)
        result = extract_json(response)
        
        return result.get('similarity_score', 0.0)
    
    async def detect_conflict_type(self, entry1: MemoryEntry, entry2: MemoryEntry) -> str:
        """
        Detect the type of conflict between two memory entries
        
        Args:
            entry1: First memory entry
            entry2: Second memory entry
            
        Returns:
            Conflict type: "compatible", "contradictory", "subsumes", "subsumed", or "unrelated"
        """
        content1 = f"Title: {entry1.title}\nSummary: {entry1.content.get('summary', 'N/A')}\nText: {entry1.content.get('text', 'N/A')[:500]}"
        content2 = f"Title: {entry2.title}\nSummary: {entry2.content.get('summary', 'N/A')}\nText: {entry2.content.get('text', 'N/A')[:500]}"
        
        prompt = f"""You are an expert at analyzing relationships between document sections.

Analyze the relationship between these two memory entries:

Entry 1 (ID: {entry1.node_id}):
{content1}

Entry 2 (ID: {entry2.node_id}):
{content2}

Determine the relationship type:
- "compatible": Both entries can coexist; they complement each other
- "contradictory": Entries contain conflicting information
- "subsumes": Entry 1 contains all information from Entry 2 and more
- "subsumed": Entry 2 contains all information from Entry 1 and more
- "unrelated": Entries are about different topics

Return a JSON object:
{{
    "conflict_type": <one of: "compatible", "contradictory", "subsumes", "subsumed", "unrelated">,
    "confidence": <float between 0 and 1>,
    "reasoning": <brief explanation>
}}

Directly return the JSON structure. Do not output anything else."""

        response = await ChatGPT_API_async(model=self.model, prompt=prompt)
        result = extract_json(response)
        
        return result.get('conflict_type', 'unrelated')
    
    async def resolve_conflict(self, entry1: MemoryEntry, entry2: MemoryEntry, 
                              conflict_type: str) -> Dict:
        """
        Resolve conflict between two memory entries using LLM-guided strategy
        
        Args:
            entry1: First memory entry
            entry2: Second memory entry
            conflict_type: Type of conflict detected
            
        Returns:
            Resolution result with action and updated entries
        """
        if conflict_type == "unrelated":
            return {
                'action': 'keep_both',
                'entries': [entry1, entry2],
                'reasoning': 'Entries are unrelated and can coexist'
            }
        
        if conflict_type == "compatible":
            return {
                'action': 'keep_both',
                'entries': [entry1, entry2],
                'reasoning': 'Entries are compatible and complement each other'
            }
        
        if conflict_type == "contradictory":
            # Keep the one with higher importance or more recent access
            if entry1.importance_score > entry2.importance_score:
                return {
                    'action': 'keep_first',
                    'entries': [entry1],
                    'removed': [entry2.node_id],
                    'reasoning': 'Entry 1 has higher importance score in contradictory conflict'
                }
            elif entry2.importance_score > entry1.importance_score:
                return {
                    'action': 'keep_second',
                    'entries': [entry2],
                    'removed': [entry1.node_id],
                    'reasoning': 'Entry 2 has higher importance score in contradictory conflict'
                }
            else:
                # If importance is equal, keep the more recently accessed one
                if entry1.last_accessed > entry2.last_accessed:
                    return {
                        'action': 'keep_first',
                        'entries': [entry1],
                        'removed': [entry2.node_id],
                        'reasoning': 'Entry 1 is more recently accessed in contradictory conflict'
                    }
                else:
                    return {
                        'action': 'keep_second',
                        'entries': [entry2],
                        'removed': [entry1.node_id],
                        'reasoning': 'Entry 2 is more recently accessed in contradictory conflict'
                    }
        
        if conflict_type == "subsumes":
            return {
                'action': 'keep_first',
                'entries': [entry1],
                'removed': [entry2.node_id],
                'reasoning': 'Entry 1 subsumes Entry 2 - keeping more comprehensive entry'
            }
        
        if conflict_type == "subsumed":
            return {
                'action': 'keep_second',
                'entries': [entry2],
                'removed': [entry1.node_id],
                'reasoning': 'Entry 2 subsumes Entry 1 - keeping more comprehensive entry'
            }
        
        # Default: keep both
        return {
            'action': 'keep_both',
            'entries': [entry1, entry2],
            'reasoning': 'Unable to determine conflict resolution - keeping both'
        }
    
    async def find_conflicts(self, entries: List[MemoryEntry]) -> List[Tuple[MemoryEntry, MemoryEntry, float]]:
        """
        Find all conflicting pairs in a list of memory entries
        
        Args:
            entries: List of memory entries to check
            
        Returns:
            List of tuples (entry1, entry2, similarity_score) for conflicting pairs
        """
        conflicts = []
        
        # Create tasks for parallel similarity calculation
        tasks = []
        pairs = []
        
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                tasks.append(self.calculate_semantic_similarity(entries[i], entries[j]))
                pairs.append((entries[i], entries[j]))
        
        # Execute all similarity calculations in parallel
        similarities = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter for conflicts above threshold
        for (entry1, entry2), similarity in zip(pairs, similarities):
            if isinstance(similarity, Exception):
                continue
            if similarity >= self.similarity_threshold:
                conflicts.append((entry1, entry2, similarity))
        
        return conflicts
    
    async def resolve_all_conflicts(self, entries: List[MemoryEntry]) -> Dict:
        """
        Detect and resolve all conflicts in a list of memory entries
        
        Args:
            entries: List of memory entries to check and resolve
            
        Returns:
            Dictionary with resolution results and updated entries
        """
        # Find all conflicts
        conflicts = await self.find_conflicts(entries)
        
        if not conflicts:
            return {
                'conflicts_found': 0,
                'resolutions': [],
                'entries': entries,
                'removed': []
            }
        
        # Resolve each conflict
        resolutions = []
        removed_ids = set()
        
        for entry1, entry2, similarity in conflicts:
            # Skip if either entry was already removed
            if entry1.node_id in removed_ids or entry2.node_id in removed_ids:
                continue
            
            # Detect conflict type
            conflict_type = await self.detect_conflict_type(entry1, entry2)
            
            # Resolve conflict
            resolution = await self.resolve_conflict(entry1, entry2, conflict_type)
            resolution['similarity'] = similarity
            resolution['conflict_type'] = conflict_type
            
            # Track removed entries
            if 'removed' in resolution:
                removed_ids.update(resolution['removed'])
            
            resolutions.append(resolution)
        
        # Filter out removed entries
        final_entries = [e for e in entries if e.node_id not in removed_ids]
        
        return {
            'conflicts_found': len(conflicts),
            'resolutions': resolutions,
            'entries': final_entries,
            'removed': list(removed_ids)
        }
