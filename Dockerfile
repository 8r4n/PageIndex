# Use existing Fedora dev container from GitHub packages
FROM ghcr.io/8r4n/fedora-dev:latest

# Set working directory
WORKDIR /app

# Install Python and pip if not already available
RUN dnf install -y python3 python3-pip && \
    dnf clean all

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

# Copy PageIndex application files
COPY pageindex/ ./pageindex/
COPY run_pageindex.py .
COPY cookbook/ ./cookbook/
COPY tutorials/ ./tutorials/

# Create results directory
RUN mkdir -p /app/results

# Set environment variable for API key (will be overridden by runtime config)
ENV CHATGPT_API_KEY=""

# Volume for input/output files
VOLUME ["/app/data", "/app/results"]

# Default command to run PageIndex with help
CMD ["python3", "run_pageindex.py", "--help"]
