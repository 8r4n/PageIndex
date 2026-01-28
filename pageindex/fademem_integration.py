"""
FadeMem Integration Module for PageIndex

This module integrates all FadeMem memory management features into PageIndex,
providing a unified interface for biologically-inspired memory management.
"""

import asyncio
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .memory_manager import MemoryManager, MemoryEntry
from .conflict_resolver import ConflictResolver
from .memory_fusion import MemoryFusion
from .query_prioritization import QueryPrioritization
from .benchmarks import BenchmarkMetrics, DashboardGenerator
from .utils import structure_to_list
import time
import threading


class FadeMemPageIndex:
    """
    Integrates FadeMem memory management with PageIndex
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize FadeMem-PageIndex integration
        
        Args:
            config_path: Path to FadeMem configuration file
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent / "fademem_config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        memory_config = {
            'lml_threshold': self.config['memory']['lml_threshold'],
            'sml_threshold': self.config['memory']['sml_threshold'],
            'pruning_threshold': self.config['memory']['pruning_threshold'],
            'dormancy_threshold': self.config['memory']['dormancy_threshold_days'] * 86400
        }
        
        self.memory_manager = MemoryManager(config=memory_config)
        self.conflict_resolver = ConflictResolver(
            model=self.config['conflict']['model'],
            similarity_threshold=self.config['conflict']['similarity_threshold']
        )
        self.memory_fusion = MemoryFusion(
            model=self.config['fusion']['model'],
            cluster_threshold=self.config['fusion']['cluster_threshold']
        )
        self.query_prioritization = QueryPrioritization(
            model=self.config['query']['model']
        )
        self.benchmarks = BenchmarkMetrics()
        self.dashboard = DashboardGenerator()
        
        # Maintenance thread
        self.maintenance_thread = None
        self.stop_maintenance = False
        
        # Operation counter for benchmark reports
        self.operation_count = 0
        
    def load_pageindex_structure(self, structure: Dict) -> int:
        """
        Load PageIndex tree structure into FadeMem memory system
        
        Args:
            structure: PageIndex tree structure (from page_index_main)
            
        Returns:
            Number of entries loaded
        """
        # Convert structure to flat list of nodes
        nodes = structure_to_list(structure)
        
        # Store baseline for SRR calculation
        self.benchmarks.baseline_size = len(nodes)
        
        # Add each node as a memory entry
        for node in nodes:
            node_id = node.get('node_id', str(hash(node.get('title', ''))))
            title = node.get('title', 'Untitled')
            
            # Calculate initial importance based on node properties
            importance = self._calculate_initial_importance(node)
            
            self.memory_manager.add_entry(
                node_id=node_id,
                title=title,
                content=node,
                importance_score=importance
            )
        
        return len(nodes)
    
    def _calculate_initial_importance(self, node: Dict) -> float:
        """Calculate initial importance score for a node"""
        # Base importance
        importance = 0.5
        
        # Boost importance for nodes with summaries (more informative)
        if node.get('summary'):
            importance += 0.1
        
        # Boost importance for top-level nodes (shallower in hierarchy)
        if 'node_id' in node:
            # Assume node_id format like "0001", "0002", etc for top level
            # and "0001.0001" for children
            depth = node['node_id'].count('.')
            importance += max(0, 0.2 - (depth * 0.05))
        
        # Normalize to [0, 1]
        return min(1.0, max(0.0, importance))
    
    async def apply_memory_management(self, enable_fusion: bool = True, 
                                      enable_conflict_resolution: bool = True,
                                      enable_pruning: bool = True) -> Dict:
        """
        Apply all memory management operations
        
        Args:
            enable_fusion: Whether to enable memory fusion
            enable_conflict_resolution: Whether to enable conflict resolution
            enable_pruning: Whether to enable pruning
            
        Returns:
            Summary of operations performed
        """
        operations = {
            'decay_applied': False,
            'promotions_demotions': False,
            'conflicts_resolved': 0,
            'entries_fused': 0,
            'entries_pruned': 0
        }
        
        # Apply decay to all entries
        self.memory_manager.apply_decay_to_all()
        operations['decay_applied'] = True
        
        # Check and perform promotions/demotions
        self.memory_manager.check_promotions_demotions()
        operations['promotions_demotions'] = True
        
        # Conflict resolution
        if enable_conflict_resolution:
            all_entries = self.memory_manager.get_all_entries(sort_by_importance=False)
            if len(all_entries) > 1:
                conflict_result = await self.conflict_resolver.resolve_all_conflicts(all_entries)
                operations['conflicts_resolved'] = conflict_result['conflicts_found']
                
                # Remove resolved conflicts from memory
                for node_id in conflict_result['removed']:
                    if node_id in self.memory_manager.lml:
                        del self.memory_manager.lml[node_id]
                    elif node_id in self.memory_manager.sml:
                        del self.memory_manager.sml[node_id]
        
        # Memory fusion
        if enable_fusion:
            # Fuse SML entries to reduce redundancy
            sml_entries = self.memory_manager.get_entries_by_layer("SML")
            if len(sml_entries) > 1:
                fusion_result = await self.memory_fusion.fuse_related_entries(sml_entries)
                operations['entries_fused'] = fusion_result['entries_before'] - fusion_result['entries_after']
                
                # Update SML with fused entries
                self.memory_manager.sml = {e.node_id: e for e in fusion_result['fused_entries']}
        
        # Pruning
        if enable_pruning:
            pruned_strength = self.memory_manager.prune_low_strength_entries()
            pruned_dormant = self.memory_manager.prune_dormant_entries()
            operations['entries_pruned'] = len(pruned_strength) + len(pruned_dormant)
        
        # Update operation counter and generate report if needed
        self.operation_count += 1
        if (self.config['benchmarks']['auto_generate_reports'] and 
            self.operation_count % self.config['benchmarks']['report_frequency'] == 0):
            self.generate_benchmark_report()
        
        return operations
    
    async def query(self, query_text: str, top_k: int = 5, 
                   layer_preference: Optional[str] = None) -> Dict:
        """
        Query the memory system with enhanced prioritization
        
        Args:
            query_text: Query string
            top_k: Number of top results to return
            layer_preference: Optional preference for "LML" or "SML"
            
        Returns:
            Query results with prioritized entries
        """
        all_entries = self.memory_manager.get_all_entries(sort_by_importance=False)
        
        results = await self.query_prioritization.retrieve_with_prioritization(
            query=query_text,
            entries=all_entries,
            top_k=top_k,
            layer_preference=layer_preference
        )
        
        return results
    
    def generate_benchmark_report(self, save_html: bool = True, 
                                  html_path: str = "./results/fademem_dashboard.html") -> Dict:
        """
        Generate benchmark report and optionally save dashboard
        
        Args:
            save_html: Whether to save HTML dashboard
            html_path: Path to save HTML dashboard
            
        Returns:
            Benchmark report
        """
        report = self.benchmarks.generate_benchmark_report(
            memory_manager=self.memory_manager,
            baseline_size=self.benchmarks.baseline_size
        )
        
        # Print text dashboard
        print(self.dashboard.generate_text_dashboard(report))
        
        # Save HTML dashboard if requested
        if save_html:
            self.dashboard.generate_html_dashboard(report, html_path)
            print(f"HTML dashboard saved to: {html_path}")
        
        return report
    
    def start_auto_maintenance(self):
        """Start automatic maintenance thread"""
        if self.maintenance_thread is not None:
            return
        
        def maintenance_loop():
            while not self.stop_maintenance:
                time.sleep(self.config['general']['maintenance_interval'])
                if self.config['general']['auto_maintenance']:
                    # Run maintenance in event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.apply_memory_management())
                    loop.close()
        
        self.maintenance_thread = threading.Thread(target=maintenance_loop, daemon=True)
        self.maintenance_thread.start()
    
    def stop_auto_maintenance(self):
        """Stop automatic maintenance thread"""
        self.stop_maintenance = True
        if self.maintenance_thread is not None:
            self.maintenance_thread.join(timeout=5)
            self.maintenance_thread = None
    
    def save_state(self, filepath: str = "./results/fademem_state.json"):
        """Save memory state to file"""
        self.memory_manager.save_to_file(filepath)
        print(f"Memory state saved to: {filepath}")
    
    def load_state(self, filepath: str = "./results/fademem_state.json"):
        """Load memory state from file"""
        self.memory_manager.load_from_file(filepath)
        print(f"Memory state loaded from: {filepath}")
    
    def get_memory_stats(self) -> Dict:
        """Get current memory statistics"""
        return self.memory_manager.get_stats()
    
    def export_structure(self) -> List[Dict]:
        """
        Export current memory state as PageIndex-compatible structure
        
        Returns:
            List of nodes in PageIndex format
        """
        all_entries = self.memory_manager.get_all_entries(sort_by_importance=True)
        
        # Convert back to PageIndex format
        structure = []
        for entry in all_entries:
            node = entry.content.copy()
            # Add FadeMem metadata
            node['fademem_metadata'] = {
                'importance_score': entry.importance_score,
                'layer': entry.layer,
                'strength': entry.strength,
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed
            }
            structure.append(node)
        
        return structure
