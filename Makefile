# Makefile for PageIndex container operations

.PHONY: help build build-alt run setup clean test-setup

# Default target
help:
	@echo "PageIndex Container Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  setup       - Initial setup (create .env, directories)"
	@echo "  build       - Build container using custom Fedora dev image"
	@echo "  build-alt   - Build container using official Fedora image"
	@echo "  test-setup  - Test container setup"
	@echo "  run         - Run container with example PDF (requires PDF_PATH)"
	@echo "  shell       - Open interactive shell in container"
	@echo "  clean       - Remove built images and temporary files"
	@echo ""
	@echo "Examples:"
	@echo "  make setup"
	@echo "  make build"
	@echo "  make run PDF_PATH=data/document.pdf"
	@echo "  make shell"

# Initial setup
setup:
	@echo "Setting up PageIndex container environment..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file - please edit and add your OpenAI API key"; \
	else \
		echo "✓ .env file already exists"; \
	fi
	@mkdir -p data results
	@echo "✓ Created data/ and results/ directories"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env and add your CHATGPT_API_KEY"
	@echo "2. Run 'make build' to build the container"
	@echo "3. Place PDF files in data/ directory"
	@echo "4. Run 'make run PDF_PATH=data/your-file.pdf'"

# Build using custom Fedora dev image
build:
	@echo "Building PageIndex container using custom Fedora dev image..."
	docker build -t pageindex:latest .

# Build using official Fedora image
build-alt:
	@echo "Building PageIndex container using official Fedora image..."
	docker build -f Dockerfile.fedora -t pageindex:latest .

# Test setup
test-setup:
	@./test-container-setup.sh

# Run container on a PDF file
run:
ifndef PDF_PATH
	@echo "Error: PDF_PATH not specified"
	@echo "Usage: make run PDF_PATH=data/your-file.pdf"
	@exit 1
endif
	@if [ ! -f $(PDF_PATH) ]; then \
		echo "Error: File $(PDF_PATH) not found"; \
		exit 1; \
	fi
	@echo "Processing $(PDF_PATH)..."
	@PDF_FILE=$$(basename $(PDF_PATH)); \
	docker run --rm \
		-v $$(pwd)/data:/app/data \
		-v $$(pwd)/results:/app/results \
		--env-file .env \
		pageindex:latest \
		python3 run_pageindex.py --pdf_path /app/data/$$PDF_FILE

# Interactive shell
shell:
	@echo "Opening interactive shell in PageIndex container..."
	docker run -it --rm \
		-v $$(pwd)/data:/app/data \
		-v $$(pwd)/results:/app/results \
		--env-file .env \
		pageindex:latest \
		/bin/bash

# Clean up
clean:
	@echo "Cleaning up PageIndex container artifacts..."
	docker rmi pageindex:latest 2>/dev/null || true
	@echo "✓ Removed pageindex:latest image"
	@echo ""
	@echo "Note: data/ and results/ directories are preserved."
	@echo "To remove them manually, run: rm -rf data/ results/"
