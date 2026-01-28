"""
FadeMem-PageIndex Example Usage

This script demonstrates how to use the FadeMem memory management features
with PageIndex for biologically-inspired document indexing and retrieval.
"""

import asyncio
import argparse
import os
from pageindex import page_index_main, FadeMemPageIndex, config

async def main():
    parser = argparse.ArgumentParser(description='FadeMem-PageIndex Example')
    parser.add_argument('--pdf_path', type=str, required=True, help='Path to PDF file')
    parser.add_argument('--model', type=str, default='gpt-4o-2024-11-20', help='Model to use')
    parser.add_argument('--query', type=str, help='Optional query to test retrieval')
    parser.add_argument('--enable-fusion', action='store_true', help='Enable memory fusion')
    parser.add_argument('--enable-conflict-resolution', action='store_true', help='Enable conflict resolution')
    parser.add_argument('--enable-pruning', action='store_true', help='Enable time-based pruning')
    parser.add_argument('--dashboard-path', type=str, default='./results/fademem_dashboard.html',
                       help='Path to save HTML dashboard')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("FadeMem-PageIndex: Biologically-Inspired Memory Management Demo")
    print("=" * 80)
    
    # Step 1: Generate PageIndex structure
    print("\n[1/6] Generating PageIndex structure from PDF...")
    opt = config(
        model=args.model,
        toc_check_page_num=20,
        max_page_num_each_node=10,
        max_token_num_each_node=20000,
        if_add_node_id="yes",
        if_add_node_summary="yes",
        if_add_doc_description="no"
    )
    
    structure = page_index_main(args.pdf_path, opt)
    print(f"✓ Generated structure with nodes")
    
    # Step 2: Initialize FadeMem system
    print("\n[2/6] Initializing FadeMem memory management system...")
    fademem = FadeMemPageIndex()
    
    # Step 3: Load structure into memory system
    print("\n[3/6] Loading PageIndex structure into dual-layer memory...")
    num_entries = fademem.load_pageindex_structure(structure)
    print(f"✓ Loaded {num_entries} entries into memory system")
    
    # Display initial stats
    initial_stats = fademem.get_memory_stats()
    print(f"  - LML entries: {initial_stats['lml_entries']}")
    print(f"  - SML entries: {initial_stats['sml_entries']}")
    
    # Step 4: Apply memory management
    print("\n[4/6] Applying memory management operations...")
    print("  - Adaptive forgetting with exponential decay")
    print("  - Promotion/demotion between LML and SML")
    if args.enable_fusion:
        print("  - Dynamic memory fusion")
    if args.enable_conflict_resolution:
        print("  - Conflict resolution")
    if args.enable_pruning:
        print("  - Time-based pruning")
    
    operations = await fademem.apply_memory_management(
        enable_fusion=args.enable_fusion,
        enable_conflict_resolution=args.enable_conflict_resolution,
        enable_pruning=args.enable_pruning
    )
    
    print(f"✓ Operations completed:")
    print(f"  - Decay applied: {operations['decay_applied']}")
    print(f"  - Promotions/demotions: {operations['promotions_demotions']}")
    print(f"  - Conflicts resolved: {operations['conflicts_resolved']}")
    print(f"  - Entries fused: {operations['entries_fused']}")
    print(f"  - Entries pruned: {operations['entries_pruned']}")
    
    # Step 5: Test query if provided
    if args.query:
        print(f"\n[5/6] Testing enhanced query prioritization...")
        print(f"Query: '{args.query}'")
        
        results = await fademem.query(args.query, top_k=5)
        
        print(f"\n✓ Top {results['top_k']} results:")
        for i, result in enumerate(results['results'], 1):
            print(f"\n  {i}. {result['title']}")
            print(f"     Node ID: {result['node_id']}")
            print(f"     Layer: {result['layer']}")
            print(f"     Score: {result['score']:.3f}")
            print(f"     Importance: {result['importance_score']:.3f}")
            print(f"     Strength: {result['strength']:.3f}")
            print(f"     Summary: {result['summary'][:100]}...")
        
        print(f"\n  Layer distribution in results:")
        print(f"    - LML: {results['layer_distribution']['LML']}")
        print(f"    - SML: {results['layer_distribution']['SML']}")
    else:
        print("\n[5/6] Skipping query test (no query provided)")
    
    # Step 6: Generate benchmark report and dashboard
    print(f"\n[6/6] Generating performance benchmarks and dashboard...")
    report = fademem.generate_benchmark_report(
        save_html=True,
        html_path=args.dashboard_path
    )
    
    print(f"\n✓ Benchmark report generated")
    print(f"  HTML dashboard saved to: {args.dashboard_path}")
    
    # Save memory state
    state_path = './results/fademem_state.json'
    fademem.save_state(state_path)
    
    print("\n" + "=" * 80)
    print("FadeMem-PageIndex demo completed successfully!")
    print("=" * 80)
    print(f"\nGenerated files:")
    print(f"  - Memory state: {state_path}")
    print(f"  - Dashboard: {args.dashboard_path}")
    
    # Export enhanced structure
    enhanced_structure = fademem.export_structure()
    print(f"  - Enhanced structure with {len(enhanced_structure)} entries")


if __name__ == "__main__":
    asyncio.run(main())
