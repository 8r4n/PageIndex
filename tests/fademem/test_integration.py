"""
Integration test demonstrating FadeMem features
This test demonstrates the complete workflow without requiring a PDF file
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from pageindex import FadeMemPageIndex

async def test_fademem_integration():
    """Test FadeMem integration with synthetic data"""
    
    print("=" * 80)
    print("FadeMem Integration Test")
    print("=" * 80)
    
    # Initialize FadeMem
    print("\n[1/5] Initializing FadeMem memory management system...")
    fademem = FadeMemPageIndex()
    print("✓ FadeMem initialized")
    
    # Create synthetic structure (simulating PageIndex output)
    print("\n[2/5] Creating synthetic document structure...")
    structure = [
        {
            'node_id': '0001',
            'title': 'Introduction to Machine Learning',
            'summary': 'Overview of machine learning concepts and applications',
            'start_index': 1,
            'end_index': 5
        },
        {
            'node_id': '0002',
            'title': 'Deep Learning Basics',
            'summary': 'Introduction to neural networks and deep learning',
            'start_index': 6,
            'end_index': 10
        },
        {
            'node_id': '0003',
            'title': 'Advanced Neural Networks',
            'summary': 'Advanced topics in neural network architectures',
            'start_index': 11,
            'end_index': 15
        },
        {
            'node_id': '0004',
            'title': 'Reinforcement Learning',
            'summary': 'Introduction to reinforcement learning algorithms',
            'start_index': 16,
            'end_index': 20
        },
        {
            'node_id': '0005',
            'title': 'Natural Language Processing',
            'summary': 'NLP techniques and applications in machine learning',
            'start_index': 21,
            'end_index': 25
        }
    ]
    
    # Load into memory system
    print("\n[3/5] Loading structure into dual-layer memory...")
    num_entries = fademem.load_pageindex_structure(structure)
    print(f"✓ Loaded {num_entries} entries")
    
    # Display initial statistics
    stats = fademem.get_memory_stats()
    print(f"\nInitial Memory Statistics:")
    print(f"  - Total entries: {stats['total_entries']}")
    print(f"  - LML entries: {stats['lml_entries']}")
    print(f"  - SML entries: {stats['sml_entries']}")
    
    # Apply memory management (without LLM features to avoid API calls)
    print("\n[4/5] Applying memory management operations...")
    print("  - Adaptive forgetting with exponential decay")
    print("  - Promotion/demotion between LML and SML")
    
    # Apply only decay and promotion/demotion (skip LLM-dependent features)
    operations = await fademem.apply_memory_management(
        enable_fusion=False,  # Requires LLM
        enable_conflict_resolution=False,  # Requires LLM
        enable_pruning=True
    )
    
    print(f"✓ Operations completed:")
    print(f"  - Decay applied: {operations['decay_applied']}")
    print(f"  - Promotions/demotions: {operations['promotions_demotions']}")
    print(f"  - Entries pruned: {operations['entries_pruned']}")
    
    # Display updated statistics
    stats = fademem.get_memory_stats()
    print(f"\nUpdated Memory Statistics:")
    print(f"  - Total entries: {stats['total_entries']}")
    print(f"  - LML entries: {stats['lml_entries']}")
    print(f"  - SML entries: {stats['sml_entries']}")
    
    # Generate benchmark report
    print("\n[5/5] Generating performance benchmarks...")
    report = fademem.generate_benchmark_report(save_html=False)
    
    print(f"\n✓ Benchmark Metrics:")
    metrics = report['metrics']
    print(f"  - Storage Reduction Rate: {metrics['storage_reduction_rate']:.2f}%")
    print(f"  - Temporal Consistency Score: {metrics['temporal_consistency_score']:.3f}")
    print(f"  - Layer Distribution Balance: {metrics['layer_distribution_balance']:.3f}")
    print(f"  - Average Strength: {metrics['avg_strength']:.3f}")
    print(f"  - Average Importance: {metrics['avg_importance']:.3f}")
    
    print("\n" + "=" * 80)
    print("FadeMem Integration Test Completed Successfully!")
    print("=" * 80)
    
    # Test state persistence
    print("\n[Bonus] Testing state persistence...")
    state_file = '/tmp/fademem_test_state.json'
    fademem.save_state(state_file)
    
    # Load state
    fademem2 = FadeMemPageIndex()
    fademem2.load_state(state_file)
    
    stats2 = fademem2.get_memory_stats()
    print(f"✓ State loaded successfully: {stats2['total_entries']} entries")
    
    # Clean up
    os.remove(state_file)
    print("✓ Test cleanup complete")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_fademem_integration())
    sys.exit(0 if result else 1)
