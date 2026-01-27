# PageIndex Container Usage

This directory contains Docker configuration files to run PageIndex in a containerized environment using a Fedora-based development container.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier management)
- OpenAI API key
- Access to `ghcr.io/8r4n/fedora-dev` container image (or use alternative Dockerfile)

## Authentication for GitHub Container Registry

If the base Fedora dev container image is private, authenticate to GitHub Container Registry:

```bash
# Create a GitHub Personal Access Token with read:packages permission
# Then authenticate:
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

## Build Options

### Option 1: Using Custom Fedora Dev Container (Default)

The default `Dockerfile` uses your existing Fedora dev container from GitHub packages:

```bash
docker build -t pageindex:latest .
```

### Option 2: Using Official Fedora Base Image

If you don't have access to the custom Fedora dev container, use the alternative Dockerfile:

```bash
docker build -f Dockerfile.fedora -t pageindex:latest .
```

## Quick Start

### Using Makefile (Recommended)

The easiest way to get started is using the provided Makefile:

```bash
# Initial setup
make setup

# Edit .env to add your OpenAI API key
nano .env

# Build the container
make build

# Process a PDF
make run PDF_PATH=data/document.pdf
```

### Manual Setup

### 1. Set up your environment

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and replace `your_openai_key_here` with your actual OpenAI API key.

### 2. Build the container

```bash
docker build -t pageindex:latest .
```

Or using docker-compose:

```bash
docker-compose build
```

### 3. Process a PDF document

Create a `data` directory and place your PDF files there:

```bash
mkdir -p data
cp /path/to/your/document.pdf data/
```

Run PageIndex on your document:

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  --env-file .env \
  pageindex:latest \
  python3 run_pageindex.py --pdf_path /app/data/document.pdf
```

Or using docker-compose:

```bash
docker-compose run --rm pageindex \
  python3 run_pageindex.py --pdf_path /app/data/document.pdf
```

### 4. View results

The generated tree structure will be saved in the `results/` directory:

```bash
cat results/document_structure.json
```

## Advanced Usage

### Process Markdown files

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  --env-file .env \
  pageindex:latest \
  python3 run_pageindex.py --md_path /app/data/document.md
```

### Custom options

You can pass additional options to PageIndex:

```bash
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  --env-file .env \
  pageindex:latest \
  python3 run_pageindex.py \
    --pdf_path /app/data/document.pdf \
    --model gpt-4o-2024-11-20 \
    --max-pages-per-node 15 \
    --if-add-node-summary yes
```

### Interactive shell

To explore the container interactively:

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  --env-file .env \
  pageindex:latest \
  /bin/bash
```

## Volume Mounts

The container uses two volume mounts:

- `/app/data`: Input directory for PDF and Markdown files
- `/app/results`: Output directory for generated tree structures

## Base Image

This container is built on top of the Fedora dev container image from GitHub packages:
- `ghcr.io/8r4n/fedora-dev:latest`

## Troubleshooting

### API Key not found

If you get an error about missing API key, make sure:
1. The `.env` file exists and contains `CHATGPT_API_KEY=your_actual_key`
2. You're using `--env-file .env` flag with `docker run`

### Permission issues

If you encounter permission issues with mounted volumes:

```bash
# On Linux/Mac, you might need to adjust permissions
chmod -R 755 data results
```

### Container build fails

If the base Fedora dev container is not accessible, verify:
1. You have access to the `ghcr.io/8r4n/fedora-dev` package
2. You're authenticated to GitHub Container Registry if needed:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

If you see SSL certificate errors during build, this is typically a network/environment issue. Try:
- Building from a different network
- Using the alternative Dockerfile: `docker build -f Dockerfile.fedora -t pageindex:latest .`
- Checking your Docker daemon's network settings

## Examples

See the main [README.md](README.md) for detailed examples and usage patterns.

## Support

For issues and questions, please refer to the main repository documentation or open an issue.
