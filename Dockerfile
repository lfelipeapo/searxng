# Use Ubuntu como base
FROM ubuntu:22.04

# Defina variáveis de ambiente
ENV SEARXNG_HOME=/srv/searxng

# Defina o fuso horário
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
    echo "America/Sao_Paulo" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata

# Atualize o sistema e instale o Python 3.9 e outras dependências
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3.9 \
    python3-pip \
    git \
    uwsgi \
    sudo \
    systemctl \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crie um usuário não-root
RUN useradd -m searxng

# Clone o repositório do SearXNG
RUN git clone https://github.com/lfelipeapo/searxng.git $SEARXNG_HOME

# Defina o diretório de trabalho
WORKDIR $SEARXNG_HOME

# Adicione o diretório do repositório à lista de diretórios seguros do Git
RUN git config --global --add safe.directory /srv/searxng

# Instale o SearXNG e suas dependências
RUN chmod +x ./utils/searxng.sh && \
    ./utils/searxng.sh install searxng-src && \
    ./utils/searxng.sh install pyenv && \
    ./utils/searxng.sh install settings && \
    ./utils/searxng.sh install uwsgi && \
    ./utils/searxng.sh install all

# Exponha as portas necessárias
EXPOSE 8080

# Comando para executar o SearXNG
CMD ["uwsgi", "--ini", "searxng.ini"]
