FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-babel \
    python3-venv \
    uwsgi \
    uwsgi-plugin-python3 \
    git \
    build-essential \
    libxslt-dev \
    zlib1g-dev \
    libffi-dev \
    libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create user and directory structure
RUN useradd --shell /bin/bash --system --home-dir /usr/local/searxng --comment 'Privacy-respecting metasearch engine' searxng && \
    mkdir -p /usr/local/searxng && \
    chown -R searxng:searxng /usr/local/searxng

# Switch to non-root user
USER searxng

# Set working directory
WORKDIR /usr/local/searxng

# Clone SearXNG repository
RUN git clone https://github.com/searxng/searxng /usr/local/searxng/searxng-src

# Set up Python virtual environment
RUN python3 -m venv /usr/local/searxng/searx-pyenv && \
    echo ". /usr/local/searxng/searx-pyenv/bin/activate" >> ~/.bashrc

# Activate virtual environment and install dependencies
RUN /usr/local/searxng/searx-pyenv/bin/pip install -U pip setuptools wheel pyyaml && \
    cd /usr/local/searxng/searxng-src && \
    /usr/local/searxng/searx-pyenv/bin/pip install -e . --use-pep517 --no-build-isolation -r requirements.txt

# Install additional dependencies
RUN /usr/local/searxng/searx-pyenv/bin/pip install uwsgi

# Expose the port
EXPOSE 8888

# Start the application
CMD ["/bin/bash", "-c", "source /usr/local/searxng/searx-pyenv/bin/activate && python searxng-src/searx/webapp.py"]
