FROM python:3.9-slim

# Instalar dependências do sistema
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

# Criar usuário e estrutura de diretórios
RUN useradd --shell /bin/bash --system --home-dir /usr/local/searxng --comment 'Privacy-respecting metasearch engine' searxng && \
    mkdir -p /usr/local/searxng && \
    chown -R searxng:searxng /usr/local/searxng

# Mudar para usuário não-root
USER searxng

# Definir diretório de trabalho
WORKDIR /usr/local/searxng

# Clonar repositório SearXNG
RUN git clone https://github.com/lfelipeapo/searxng /usr/local/searxng/searxng-src

# Configurar ambiente virtual
RUN python3 -m venv /usr/local/searxng/searx-pyenv

# Ativar ambiente virtual e instalar dependências
RUN . /usr/local/searxng/searx-pyenv/bin/activate && \
    pip install -U pip setuptools wheel pyyaml && \
    cd /usr/local/searxng/searxng-src && \
    pip install --use-pep517 --no-build-isolation -r requirements.txt

# Instalar dependências adicionais
RUN pip install uwsgi

# Expor porta
EXPOSE 8888

# Iniciar aplicação
CMD ["/bin/bash", "-c", ". /usr/local/searxng/searx-pyenv/bin/activate && python searxng-src/searx/webapp.py"]
