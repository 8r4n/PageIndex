"""
Performance Benchmarking Module for FadeMem-PageIndex

This module implements performance metrics including:
- Storage Reduction Rate (SRR)
- Retrieval Precision@K (RP@K)
- Temporal Consistency Score (TCS)
"""

import time
from typing import List, Dict, Optional, Tuple
from .memory_manager import MemoryEntry, MemoryManager
import json
import os


class BenchmarkMetrics:
    """
    Calculates and tracks performance metrics for memory management
    """
    
    def __init__(self):
        """Initialize benchmark metrics tracker"""
        self.metrics_history = []
        self.baseline_size = None
        
    def calculate_storage_reduction_rate(self, original_size: int, current_size: int) -> float:
        """
        Calculate Storage Reduction Rate (SRR)
        
        Args:
            original_size: Original number of entries
            current_size: Current number of entries after fusion/pruning
            
        Returns:
            SRR as a percentage
        """
        if original_size == 0:
            return 0.0
        
        srr = ((original_size - current_size) / original_size) * 100
        return srr
    
    def calculate_retrieval_precision_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        Calculate Retrieval Precision@K (RP@K)
        
        Args:
            retrieved: List of retrieved node IDs (in order)
            relevant: List of ground truth relevant node IDs
            k: Number of top results to consider
            
        Returns:
            Precision@K score between 0 and 1
        """
        if k == 0:
            return 0.0
        
        # Get top k retrieved items
        top_k = retrieved[:k]
        
        # Count how many are relevant
        relevant_in_top_k = sum(1 for node_id in top_k if node_id in relevant)
        
        # Calculate precision
        precision = relevant_in_top_k / k
        
        return precision
    
    def calculate_temporal_consistency_score(self, entries: List[MemoryEntry], 
                                            time_window: float = 86400) -> float:
        """
        Calculate Temporal Consistency Score (TCS)
        
        Measures how well the memory system maintains consistency over time.
        Higher score means entries are being accessed and maintained appropriately.
        
        Args:
            entries: List of memory entries
            time_window: Time window in seconds (default: 1 day)
            
        Returns:
            TCS score between 0 and 1
        """
        if not entries:
            return 0.0
        
        current_time = time.time()
        consistency_scores = []
        
        for entry in entries:
            # Calculate time since last access
            time_since_access = current_time - entry.last_accessed
            
            # Calculate expected strength based on time and importance
            # Higher importance should maintain strength better over time
            expected_strength = entry.importance_score * max(0, 1 - (time_since_access / time_window))
            
            # Calculate actual vs expected strength ratio
            if expected_strength > 0:
                consistency = min(1.0, entry.strength / expected_strength)
            else:
                consistency = 1.0 if entry.strength == 0 else 0.0
            
            consistency_scores.append(consistency)
        
        # Average consistency across all entries
        tcs = sum(consistency_scores) / len(consistency_scores)
        
        return tcs
    
    def calculate_layer_distribution_balance(self, lml_count: int, sml_count: int, 
                                             optimal_lml_ratio: float = 0.3) -> float:
        """
        Calculate how balanced the layer distribution is
        
        Args:
            lml_count: Number of entries in LML
            sml_count: Number of entries in SML
            optimal_lml_ratio: Optimal ratio of LML entries (default: 30%)
            
        Returns:
            Balance score between 0 and 1
        """
        total = lml_count + sml_count
        if total == 0:
            return 1.0
        
        actual_lml_ratio = lml_count / total
        
        # Calculate how far we are from optimal
        deviation = abs(actual_lml_ratio - optimal_lml_ratio)
        
        # Convert to balance score (1.0 = perfect balance, 0.0 = worst)
        balance_score = max(0.0, 1.0 - (deviation / optimal_lml_ratio))
        
        return balance_score
    
    def calculate_memory_efficiency(self, entries: List[MemoryEntry]) -> Dict[str, float]:
        """
        Calculate overall memory efficiency metrics
        
        Args:
            entries: List of memory entries
            
        Returns:
            Dictionary of efficiency metrics
        """
        if not entries:
            return {
                'avg_strength': 0.0,
                'avg_importance': 0.0,
                'strength_importance_correlation': 0.0,
                'active_ratio': 0.0
            }
        
        strengths = [e.strength for e in entries]
        importances = [e.importance_score for e in entries]
        
        avg_strength = sum(strengths) / len(strengths)
        avg_importance = sum(importances) / len(importances)
        
        # Calculate correlation between strength and importance
        # High correlation means the system is working well (important items stay strong)
        if len(entries) > 1:
            # Simple correlation using sum of products
            mean_str = avg_strength
            mean_imp = avg_importance
            
            numerator = sum((s - mean_str) * (i - mean_imp) for s, i in zip(strengths, importances))
            denominator_str = sum((s - mean_str) ** 2 for s in strengths) ** 0.5
            denominator_imp = sum((i - mean_imp) ** 2 for i in importances) ** 0.5
            
            if denominator_str > 0 and denominator_imp > 0:
                correlation = numerator / (denominator_str * denominator_imp)
            else:
                # All values are identical - perfect correlation
                correlation = 1.0
        else:
            correlation = 1.0
        
        # Calculate ratio of "active" entries (strength > 0.5)
        active_count = sum(1 for e in entries if e.strength > 0.5)
        active_ratio = active_count / len(entries)
        
        return {
            'avg_strength': avg_strength,
            'avg_importance': avg_importance,
            'strength_importance_correlation': correlation,
            'active_ratio': active_ratio
        }
    
    def generate_benchmark_report(self, memory_manager: MemoryManager, 
                                  baseline_size: Optional[int] = None,
                                  retrieval_results: Optional[Dict] = None) -> Dict:
        """
        Generate comprehensive benchmark report
        
        Args:
            memory_manager: MemoryManager instance
            baseline_size: Original size before any operations
            retrieval_results: Optional results from recent retrieval
            
        Returns:
            Comprehensive benchmark report
        """
        stats = memory_manager.get_stats()
        all_entries = memory_manager.get_all_entries(sort_by_importance=False)
        
        # Calculate SRR if baseline provided
        if baseline_size is not None:
            self.baseline_size = baseline_size
        
        if self.baseline_size is not None:
            srr = self.calculate_storage_reduction_rate(self.baseline_size, stats['total_entries'])
        else:
            srr = 0.0
        
        # Calculate TCS
        tcs = self.calculate_temporal_consistency_score(all_entries)
        
        # Calculate layer balance
        layer_balance = self.calculate_layer_distribution_balance(
            stats['lml_entries'],
            stats['sml_entries']
        )
        
        # Calculate efficiency metrics
        efficiency = self.calculate_memory_efficiency(all_entries)
        
        report = {
            'timestamp': time.time(),
            'memory_stats': stats,
            'metrics': {
                'storage_reduction_rate': srr,
                'temporal_consistency_score': tcs,
                'layer_distribution_balance': layer_balance,
                **efficiency
            }
        }
        
        # Add retrieval metrics if provided
        if retrieval_results:
            report['retrieval_metrics'] = retrieval_results
        
        # Store in history
        self.metrics_history.append(report)
        
        return report
    
    def save_metrics_history(self, filepath: str):
        """Save metrics history to file"""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metrics_history, f, indent=2)
    
    def load_metrics_history(self, filepath: str):
        """Load metrics history from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.metrics_history = json.load(f)
    
    def get_metrics_summary(self) -> Dict:
        """Get summary of metrics over time"""
        if not self.metrics_history:
            return {}
        
        recent = self.metrics_history[-1] if self.metrics_history else {}
        
        # Calculate trends if we have multiple data points
        if len(self.metrics_history) > 1:
            first = self.metrics_history[0]
            last = self.metrics_history[-1]
            
            srr_trend = last['metrics']['storage_reduction_rate'] - first['metrics']['storage_reduction_rate']
            tcs_trend = last['metrics']['temporal_consistency_score'] - first['metrics']['temporal_consistency_score']
            
            trends = {
                'srr_trend': srr_trend,
                'tcs_trend': tcs_trend
            }
        else:
            trends = {}
        
        return {
            'current_metrics': recent.get('metrics', {}),
            'total_snapshots': len(self.metrics_history),
            'trends': trends
        }


class DashboardGenerator:
    """
    Generates monitoring dashboard visualizations for memory dynamics
    """
    
    def __init__(self):
        """Initialize dashboard generator"""
        pass
    
    def generate_text_dashboard(self, benchmark_report: Dict) -> str:
        """
        Generate a text-based dashboard view
        
        Args:
            benchmark_report: Benchmark report from BenchmarkMetrics
            
        Returns:
            Formatted text dashboard
        """
        stats = benchmark_report.get('memory_stats', {})
        metrics = benchmark_report.get('metrics', {})
        
        dashboard = f"""
╔════════════════════════════════════════════════════════════════╗
║           FadeMem-PageIndex Memory Dashboard                   ║
╠════════════════════════════════════════════════════════════════╣
║ Memory Statistics:                                             ║
║   Total Entries:        {stats.get('total_entries', 0):>6}                            ║
║   LML Entries:          {stats.get('lml_entries', 0):>6} ({stats.get('lml_entries', 0) / max(stats.get('total_entries', 1), 1) * 100:>5.1f}%)                    ║
║   SML Entries:          {stats.get('sml_entries', 0):>6} ({stats.get('sml_entries', 0) / max(stats.get('total_entries', 1), 1) * 100:>5.1f}%)                    ║
║   Promotions:           {stats.get('promotions', 0):>6}                            ║
║   Demotions:            {stats.get('demotions', 0):>6}                            ║
║   Pruned:               {stats.get('pruned_entries', 0):>6}                            ║
╠════════════════════════════════════════════════════════════════╣
║ Performance Metrics:                                           ║
║   Storage Reduction Rate (SRR):        {metrics.get('storage_reduction_rate', 0):>6.2f}%        ║
║   Temporal Consistency Score (TCS):    {metrics.get('temporal_consistency_score', 0):>6.3f}         ║
║   Layer Distribution Balance:          {metrics.get('layer_distribution_balance', 0):>6.3f}         ║
║   Avg Strength:                        {metrics.get('avg_strength', 0):>6.3f}         ║
║   Avg Importance:                      {metrics.get('avg_importance', 0):>6.3f}         ║
║   Strength-Importance Correlation:     {metrics.get('strength_importance_correlation', 0):>6.3f}         ║
║   Active Entry Ratio:                  {metrics.get('active_ratio', 0):>6.3f}         ║
╚════════════════════════════════════════════════════════════════╝
"""
        return dashboard
    
    def generate_html_dashboard(self, benchmark_report: Dict, filepath: str):
        """
        Generate an HTML dashboard and save to file
        
        Args:
            benchmark_report: Benchmark report
            filepath: Path to save HTML file
        """
        stats = benchmark_report.get('memory_stats', {})
        metrics = benchmark_report.get('metrics', {})
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>FadeMem-PageIndex Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .metric-value {{ font-size: 24px; color: #4CAF50; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .card {{ background: #f9f9f9; padding: 15px; border-radius: 4px; border-left: 4px solid #4CAF50; }}
        .card-title {{ font-weight: bold; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 FadeMem-PageIndex Memory Dashboard</h1>
        
        <div class="section">
            <h2>Memory Statistics</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Total Entries</div>
                    <div class="metric-value">{stats.get('total_entries', 0)}</div>
                </div>
                <div class="card">
                    <div class="card-title">LML Entries</div>
                    <div class="metric-value">{stats.get('lml_entries', 0)} ({stats.get('lml_entries', 0) / max(stats.get('total_entries', 1), 1) * 100:.1f}%)</div>
                </div>
                <div class="card">
                    <div class="card-title">SML Entries</div>
                    <div class="metric-value">{stats.get('sml_entries', 0)} ({stats.get('sml_entries', 0) / max(stats.get('total_entries', 1), 1) * 100:.1f}%)</div>
                </div>
                <div class="card">
                    <div class="card-title">Promotions</div>
                    <div class="metric-value">{stats.get('promotions', 0)}</div>
                </div>
                <div class="card">
                    <div class="card-title">Demotions</div>
                    <div class="metric-value">{stats.get('demotions', 0)}</div>
                </div>
                <div class="card">
                    <div class="card-title">Pruned Entries</div>
                    <div class="metric-value">{stats.get('pruned_entries', 0)}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Storage Reduction Rate (SRR)</div>
                    <div class="metric-value">{metrics.get('storage_reduction_rate', 0):.2f}%</div>
                </div>
                <div class="card">
                    <div class="card-title">Temporal Consistency Score (TCS)</div>
                    <div class="metric-value">{metrics.get('temporal_consistency_score', 0):.3f}</div>
                </div>
                <div class="card">
                    <div class="card-title">Layer Distribution Balance</div>
                    <div class="metric-value">{metrics.get('layer_distribution_balance', 0):.3f}</div>
                </div>
                <div class="card">
                    <div class="card-title">Average Strength</div>
                    <div class="metric-value">{metrics.get('avg_strength', 0):.3f}</div>
                </div>
                <div class="card">
                    <div class="card-title">Average Importance</div>
                    <div class="metric-value">{metrics.get('avg_importance', 0):.3f}</div>
                </div>
                <div class="card">
                    <div class="card-title">Active Entry Ratio</div>
                    <div class="metric-value">{metrics.get('active_ratio', 0):.3f}</div>
                </div>
            </div>
        </div>
        
        <div class="section" style="margin-top: 30px; padding: 10px; background: #f0f0f0; border-radius: 4px;">
            <small>Generated at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(benchmark_report.get('timestamp', time.time())))}</small>
        </div>
    </div>
</body>
</html>"""
        
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
