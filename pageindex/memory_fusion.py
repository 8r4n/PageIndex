"""
Memory Fusion Module for FadeMem-PageIndex

This module implements dynamic memory fusion to cluster and merge semantically
related memory entries, reducing redundancy while preserving essential information.
"""

import asyncio
from typing import List, Dict, Optional
from .utils import ChatGPT_API_async, extract_json
from .memory_manager import MemoryEntry
import copy


class MemoryFusion:
    """
    Handles clustering and fusion of semantically related memory entries
    """
    
    def __init__(self, model: str = "gpt-4o-2024-11-20", cluster_threshold: float = 0.7):
        """
        Initialize memory fusion module
        
        Args:
            model: LLM model to use for fusion
            cluster_threshold: Similarity threshold for clustering (0-1)
        """
        self.model = model
        self.cluster_threshold = cluster_threshold
    
    async def calculate_similarity(self, entry1: MemoryEntry, entry2: MemoryEntry) -> float:
        """
        Calculate semantic similarity between two entries
        
        Args:
            entry1: First memory entry
            entry2: Second memory entry
            
        Returns:
            Similarity score between 0 and 1
        """
        content1 = f"Title: {entry1.title}\nSummary: {entry1.content.get('summary', 'N/A')}"
        content2 = f"Title: {entry2.title}\nSummary: {entry2.content.get('summary', 'N/A')}"
        
        prompt = f"""Calculate the semantic similarity between these two memory entries.

Entry 1:
{content1}

Entry 2:
{content2}

Return a JSON object:
{{
    "similarity": <float between 0 and 1>
}}

Directly return the JSON structure. Do not output anything else."""

        response = await ChatGPT_API_async(model=self.model, prompt=prompt)
        result = extract_json(response)
        
        return result.get('similarity', 0.0)
    
    def cluster_entries(self, entries: List[MemoryEntry], similarity_matrix: List[List[float]]) -> List[List[MemoryEntry]]:
        """
        Cluster memory entries based on similarity using simple greedy clustering
        
        Args:
            entries: List of memory entries
            similarity_matrix: Pre-calculated similarity matrix
            
        Returns:
            List of clusters, where each cluster is a list of memory entries
        """
        n = len(entries)
        visited = [False] * n
        clusters = []
        
        for i in range(n):
            if visited[i]:
                continue
            
            # Start a new cluster with entry i
            cluster = [entries[i]]
            visited[i] = True
            
            # Add similar entries to the cluster
            for j in range(i + 1, n):
                if visited[j]:
                    continue
                
                # Check if entry j is similar to any entry in the cluster
                is_similar = False
                for k in range(len(cluster)):
                    cluster_idx = entries.index(cluster[k])
                    if similarity_matrix[cluster_idx][j] >= self.cluster_threshold:
                        is_similar = True
                        break
                
                if is_similar:
                    cluster.append(entries[j])
                    visited[j] = True
            
            clusters.append(cluster)
        
        return clusters
    
    async def fuse_cluster(self, cluster: List[MemoryEntry]) -> MemoryEntry:
        """
        Fuse a cluster of memory entries into a single comprehensive entry
        
        Args:
            cluster: List of memory entries to fuse
            
        Returns:
            Fused memory entry
        """
        if len(cluster) == 1:
            return cluster[0]
        
        # Prepare cluster information for LLM
        cluster_info = []
        for i, entry in enumerate(cluster):
            info = f"""Entry {i+1} (ID: {entry.node_id}, Importance: {entry.importance_score:.2f}):
Title: {entry.title}
Summary: {entry.content.get('summary', 'N/A')}
"""
            cluster_info.append(info)
        
        cluster_text = "\n".join(cluster_info)
        
        prompt = f"""You are an expert at synthesizing information from multiple related document sections.

You are given a cluster of semantically related memory entries. Your task is to create a single, comprehensive fused entry that:
1. Preserves all unique and essential information from all entries
2. Eliminates redundancy
3. Creates a coherent, unified summary
4. Uses the most informative title

Cluster entries:
{cluster_text}

Return a JSON object:
{{
    "title": <unified title for the fused entry>,
    "summary": <comprehensive summary preserving all unique information>,
    "unique_information": [<list of key unique points preserved from each entry>]
}}

Directly return the JSON structure. Do not output anything else."""

        response = await ChatGPT_API_async(model=self.model, prompt=prompt)
        result = extract_json(response)
        
        # Create fused entry
        # Use the highest importance score from the cluster
        max_importance = max(e.importance_score for e in cluster)
        
        # Use the most recent access time
        most_recent_access = max(e.last_accessed for e in cluster)
        
        # Sum access counts
        total_access_count = sum(e.access_count for e in cluster)
        
        # Create new fused content
        fused_content = copy.deepcopy(cluster[0].content)
        fused_content['summary'] = result.get('summary', '')
        fused_content['unique_information'] = result.get('unique_information', [])
        fused_content['fused_from'] = [e.node_id for e in cluster]
        
        # Create new fused entry
        fused_entry = MemoryEntry(
            node_id=f"fused_{cluster[0].node_id}",
            title=result.get('title', cluster[0].title),
            content=fused_content,
            importance_score=max_importance,
            layer=cluster[0].layer
        )
        
        # Update temporal properties
        fused_entry.last_accessed = most_recent_access
        fused_entry.access_count = total_access_count
        
        # Combine semantic relevance scores
        all_semantic_scores = []
        for entry in cluster:
            all_semantic_scores.extend(entry.semantic_relevance_scores)
        fused_entry.semantic_relevance_scores = all_semantic_scores[-10:]  # Keep recent 10
        
        # Average the strength
        avg_strength = sum(e.strength for e in cluster) / len(cluster)
        fused_entry.strength = avg_strength
        
        return fused_entry
    
    async def fuse_related_entries(self, entries: List[MemoryEntry]) -> Dict:
        """
        Find and fuse all semantically related entries
        
        Args:
            entries: List of memory entries to process
            
        Returns:
            Dictionary with fusion results
        """
        if len(entries) <= 1:
            return {
                'clusters_found': 0,
                'entries_before': len(entries),
                'entries_after': len(entries),
                'fused_entries': entries,
                'reduction_rate': 0.0
            }
        
        # Calculate similarity matrix
        n = len(entries)
        similarity_matrix = [[0.0] * n for _ in range(n)]
        
        tasks = []
        pairs = []
        
        for i in range(n):
            for j in range(i + 1, n):
                tasks.append(self.calculate_similarity(entries[i], entries[j]))
                pairs.append((i, j))
        
        # Execute all similarity calculations in parallel
        similarities = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Fill similarity matrix
        for (i, j), similarity in zip(pairs, similarities):
            if isinstance(similarity, Exception):
                similarity = 0.0
            similarity_matrix[i][j] = similarity
            similarity_matrix[j][i] = similarity
        
        # Set diagonal to 1.0
        for i in range(n):
            similarity_matrix[i][i] = 1.0
        
        # Cluster entries
        clusters = self.cluster_entries(entries, similarity_matrix)
        
        # Fuse each cluster
        fusion_tasks = [self.fuse_cluster(cluster) for cluster in clusters]
        fused_entries = await asyncio.gather(*fusion_tasks, return_exceptions=True)
        
        # Filter out exceptions
        fused_entries = [e for e in fused_entries if not isinstance(e, Exception)]
        
        # Calculate reduction rate
        entries_before = len(entries)
        entries_after = len(fused_entries)
        reduction_rate = (entries_before - entries_after) / entries_before if entries_before > 0 else 0.0
        
        return {
            'clusters_found': len(clusters),
            'entries_before': entries_before,
            'entries_after': entries_after,
            'fused_entries': fused_entries,
            'reduction_rate': reduction_rate,
            'clusters': [
                {
                    'size': len(cluster),
                    'node_ids': [e.node_id for e in cluster]
                }
                for cluster in clusters if len(cluster) > 1
            ]
        }
