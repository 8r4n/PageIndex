# FadeMem: Biologically-Inspired Memory Management for PageIndex

## Overview

FadeMem is a biologically-inspired memory management system integrated into PageIndex, implementing features from the FadeMem paper for intelligent, adaptive document indexing and retrieval.

## Features

### 1. Dual-Layer Memory Architecture

Memory entries are organized into two hierarchical layers:

- **Long-term Memory Layer (LML)**: Stores highly important, frequently accessed entries
- **Short-term Memory Layer (SML)**: Stores less important or recently added entries

Entries are dynamically promoted or demoted between layers based on their importance scores.

### 2. Adaptive Forgetting Mechanism

Implements exponential decay for memory retention:

- **Importance-based decay**: Higher importance entries decay slower
- **Strength tracking**: Memory strength decreases over time without access
- **Dynamic thresholds**: Configurable promotion/demotion thresholds

### 3. Conflict Resolution

Detects and resolves conflicts among indexed entries:

- **Semantic similarity detection**: Identifies related or conflicting entries
- **LLM-guided resolution**: Uses AI to determine conflict types:
  - Compatible: Entries can coexist
  - Contradictory: Conflicting information
  - Subsumes/Subsumed: One entry contains the other
- **Intelligent merging**: Keeps the most relevant entry

### 4. Dynamic Memory Fusion

Reduces redundancy through intelligent clustering and fusion:

- **Semantic clustering**: Groups related entries
- **LLM-guided synthesis**: Merges clusters while preserving unique information
- **Information preservation**: Maintains essential details from all fused entries

### 5. Time-Based Pruning

Automatically removes outdated or irrelevant entries:

- **Low-strength pruning**: Removes entries with weak memory strength
- **Dormancy-based pruning**: Removes long-inactive entries
- **Layer-aware pruning**: More aggressive in SML, conservative in LML

### 6. Enhanced Query Prioritization

Intelligent retrieval based on multiple factors:

- **Semantic relevance**: How well entries match the query
- **Importance scores**: Prioritizes important entries
- **Query patterns**: Learns from query history
- **Temporal factors**: Considers recency and access patterns
- **Composite scoring**: Weighted combination of all factors

### 7. Performance Benchmarking

Comprehensive metrics and visualization:

- **Storage Reduction Rate (SRR)**: Measures compression from fusion/pruning
- **Retrieval Precision@K (RP@K)**: Measures retrieval accuracy
- **Temporal Consistency Score (TCS)**: Measures memory stability over time
- **HTML Dashboard**: Visual monitoring of memory dynamics
- **Metrics tracking**: Historical performance data

## Installation

The FadeMem features are included in the PageIndex package. No additional installation required.

## Usage

### Basic Usage

```python
import asyncio
from pageindex import page_index_main, FadeMemPageIndex, config

async def main():
    # 1. Generate PageIndex structure
    opt = config(
        model='gpt-4o-2024-11-20',
        if_add_node_summary='yes'
    )
    structure = page_index_main('document.pdf', opt)
    
    # 2. Initialize FadeMem
    fademem = FadeMemPageIndex()
    
    # 3. Load structure into memory system
    fademem.load_pageindex_structure(structure)
    
    # 4. Apply memory management
    await fademem.apply_memory_management(
        enable_fusion=True,
        enable_conflict_resolution=True,
        enable_pruning=True
    )
    
    # 5. Query with prioritization
    results = await fademem.query("What is the main topic?", top_k=5)
    
    # 6. Generate benchmark report
    fademem.generate_benchmark_report()

asyncio.run(main())
```

### Using the Command-Line Script

```bash
# Basic usage
python3 run_fademem.py --pdf_path document.pdf

# With all features enabled
python3 run_fademem.py \
    --pdf_path document.pdf \
    --enable-fusion \
    --enable-conflict-resolution \
    --enable-pruning \
    --query "What are the key findings?"

# Custom dashboard location
python3 run_fademem.py \
    --pdf_path document.pdf \
    --dashboard-path ./my_dashboard.html
```

## Configuration

Edit `pageindex/fademem_config.yaml` to customize behavior:

```yaml
memory:
  lml_threshold: 0.7      # Promotion threshold
  sml_threshold: 0.3      # Demotion threshold
  pruning_threshold: 0.1  # Strength threshold for pruning
  dormancy_threshold_days: 30

decay:
  base_decay_rate: 0.1
  importance_weights:
    recency: 0.3
    frequency: 0.3
    semantic: 0.4

conflict:
  similarity_threshold: 0.8

fusion:
  cluster_threshold: 0.7
```

## API Reference

### FadeMemPageIndex

Main class integrating all features.

```python
fademem = FadeMemPageIndex(config_path=None)
```

#### Methods

**load_pageindex_structure(structure)**
- Load PageIndex tree into memory system
- Returns: Number of entries loaded

**apply_memory_management(enable_fusion, enable_conflict_resolution, enable_pruning)**
- Apply all memory management operations
- Returns: Dictionary with operation results

**query(query_text, top_k=5, layer_preference=None)**
- Query with enhanced prioritization
- Returns: Prioritized results

**generate_benchmark_report(save_html=True, html_path)**
- Generate performance metrics
- Returns: Benchmark report dictionary

**save_state(filepath)**
- Save memory state to JSON

**load_state(filepath)**
- Load memory state from JSON

**export_structure()**
- Export as PageIndex-compatible structure

### MemoryManager

Core memory management with dual-layer architecture.

```python
manager = MemoryManager(config)
```

### ConflictResolver

Detects and resolves conflicts.

```python
resolver = ConflictResolver(model, similarity_threshold)
```

### MemoryFusion

Clusters and fuses related entries.

```python
fusion = MemoryFusion(model, cluster_threshold)
```

### QueryPrioritization

Enhanced query-based retrieval.

```python
query_system = QueryPrioritization(model)
```

### BenchmarkMetrics

Performance tracking and reporting.

```python
metrics = BenchmarkMetrics()
```

## Architecture

```
FadeMemPageIndex
├── MemoryManager (Dual-layer architecture, decay, promotion/demotion)
├── ConflictResolver (Semantic similarity, LLM-guided resolution)
├── MemoryFusion (Clustering, fusion synthesis)
├── QueryPrioritization (Importance-based retrieval)
└── BenchmarkMetrics (SRR, RP@K, TCS, dashboard)
```

## Examples

### Example 1: Memory State Persistence

```python
# Save after processing
fademem.save_state('./memory_state.json')

# Load later
fademem.load_state('./memory_state.json')
```

### Example 2: Layer-Specific Querying

```python
# Prefer LML (long-term memory)
results = await fademem.query(
    "Important historical data",
    top_k=10,
    layer_preference="LML"
)
```

### Example 3: Custom Configuration

```python
from pageindex.memory_manager import MemoryManager

# Custom thresholds
manager = MemoryManager(config={
    'lml_threshold': 0.8,
    'sml_threshold': 0.2,
    'pruning_threshold': 0.05
})
```

## Testing

Run the test suite:

```bash
python3 -m unittest tests/fademem/test_memory_manager.py
```

## Performance Metrics

### Storage Reduction Rate (SRR)

Measures memory efficiency:
```
SRR = (Original_Entries - Current_Entries) / Original_Entries × 100%
```

### Retrieval Precision@K (RP@K)

Measures retrieval accuracy:
```
RP@K = Relevant_in_Top_K / K
```

### Temporal Consistency Score (TCS)

Measures memory stability:
```
TCS = Average(Actual_Strength / Expected_Strength)
```

## Dashboard

The HTML dashboard provides real-time visualization:

- Memory statistics (total, LML, SML entries)
- Promotion/demotion counts
- Performance metrics
- Layer distribution
- Temporal trends

Access at: `./results/fademem_dashboard.html`

## Best Practices

1. **Regular Maintenance**: Apply memory management periodically
2. **Tune Thresholds**: Adjust based on your use case
3. **Monitor Metrics**: Check dashboard regularly
4. **Save State**: Persist memory for continuity
5. **Query Patterns**: Let the system learn from queries

## Limitations

- Requires OpenAI API for LLM operations
- Processing time scales with number of entries
- Memory fusion requires sufficient semantic similarity

## Future Enhancements

- Multi-document memory management
- Advanced pattern recognition in queries
- Real-time adaptive threshold adjustment
- Integration with vector databases
- Support for other LLM providers

## References

Based on the FadeMem paper's biologically-inspired memory management principles.

## License

Same as PageIndex - see LICENSE file

## Support

For issues or questions:
- GitHub Issues
- Discord community
- Documentation: docs.pageindex.ai
