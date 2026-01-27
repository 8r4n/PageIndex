#!/bin/bash
# Example usage script for PageIndex container

set -e

echo "======================================"
echo "PageIndex Container Usage Examples"
echo "======================================"
echo ""

# Check if container image exists
if ! docker image inspect pageindex:latest >/dev/null 2>&1; then
    echo "❌ PageIndex container image not found."
    echo "Please build the container first:"
    echo "  docker build -t pageindex:latest ."
    echo "  OR"
    echo "  docker build -f Dockerfile.fedora -t pageindex:latest ."
    exit 1
fi

echo "✓ PageIndex container image found"
echo ""

# Create directories if they don't exist
mkdir -p data results

# Check if there are any PDF files in data directory
pdf_count=$(find data -name "*.pdf" 2>/dev/null | wc -l)
if [ "$pdf_count" -eq 0 ]; then
    echo "⚠️  No PDF files found in data/ directory"
    echo "Please add some PDF files to data/ directory first"
    echo ""
    echo "Example:"
    echo "  cp /path/to/your/document.pdf data/"
    exit 0
fi

echo "Found $pdf_count PDF file(s) in data/ directory"
echo ""

# Get first PDF file
first_pdf=$(find data -name "*.pdf" | head -1)
pdf_name=$(basename "$first_pdf")

echo "======================================"
echo "Example 1: Process a single PDF"
echo "======================================"
printf "Processing: %s\n" "$pdf_name"
echo ""

docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/results:/app/results" \
  --env-file .env \
  pageindex:latest \
  python3 run_pageindex.py --pdf_path "/app/data/$pdf_name"

echo ""
echo "✓ Processing complete!"
printf "Results saved to: results/%s_structure.json\n" "${pdf_name%.pdf}"
echo ""

echo "======================================"
echo "Example 2: View help"
echo "======================================"
docker run --rm pageindex:latest python3 run_pageindex.py --help
echo ""

echo "======================================"
echo "Example 3: Custom options"
echo "======================================"
echo "You can use custom options like:"
echo ""
echo "docker run --rm \\"
echo "  -v \$(pwd)/data:/app/data \\"
echo "  -v \$(pwd)/results:/app/results \\"
echo "  --env-file .env \\"
echo "  pageindex:latest \\"
echo "  python3 run_pageindex.py \\"
echo "    --pdf_path /app/data/$pdf_name \\"
echo "    --model gpt-4o-2024-11-20 \\"
echo "    --max-pages-per-node 15 \\"
echo "    --if-add-node-summary yes"
echo ""

echo "======================================"
echo "For more examples, see CONTAINER.md"
echo "======================================"
