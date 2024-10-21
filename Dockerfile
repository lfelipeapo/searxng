FROM alpine:3.20

# Instale o libcap e o Git para obter informações de versão
RUN apk add --no-cache libcap git

# Copie o Tini e configure as capacidades necessárias
COPY --from=krallin/ubuntu-tini:trusty /usr/local/bin/tini /sbin/tini
RUN setcap 'cap_kill+ep' /sbin/tini

ENTRYPOINT ["/sbin/tini","--","/usr/local/searxng/dockerfiles/docker-entrypoint.sh"]

EXPOSE 8080

VOLUME /etc/searxng

ARG SEARXNG_GID=977
ARG SEARXNG_UID=977

RUN addgroup -g ${SEARXNG_GID} searxng && \
    adduser -u ${SEARXNG_UID} -D -h /usr/local/searxng -s /bin/sh -G searxng searxng

ENV INSTANCE_NAME=searxng \
    AUTOCOMPLETE= \
    BASE_URL= \
    MORTY_KEY= \
    MORTY_URL= \
    SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml \
    UWSGI_SETTINGS_PATH=/etc/searxng/uwsgi.ini \
    UWSGI_WORKERS=%k \
    UWSGI_THREADS=4 \
    PORT=8080

WORKDIR /usr/local/searxng

# Copie todos os arquivos, incluindo o diretório .git
COPY . .

# Obter informações do Git
RUN VERSION_GITCOMMIT=$(git rev-parse HEAD) && \
    SEARXNG_GIT_VERSION=$(git describe --tags --always) && \
    echo "VERSION_GITCOMMIT=${VERSION_GITCOMMIT}" >> /etc/environment && \
    echo "SEARXNG_GIT_VERSION=${SEARXNG_GIT_VERSION}" >> /etc/environment

# Defina os argumentos de build para serem usados como variáveis de ambiente
ARG VERSION_GITCOMMIT
ARG SEARXNG_GIT_VERSION

# Atribua os valores dos argumentos às variáveis de ambiente
ENV VERSION_GITCOMMIT=${VERSION_GITCOMMIT}
ENV SEARXNG_GIT_VERSION=${SEARXNG_GIT_VERSION}

# Instalar dependências de build e runtime
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    py3-setuptools \
    python3-dev \
    libffi-dev \
    libxslt-dev \
    libxml2-dev \
    openssl-dev \
    tar \
 && apk add --no-cache \
    ca-certificates \
    python3 \
    py3-pip \
    libxml2 \
    libxslt \
    openssl \
    uwsgi \
    uwsgi-python3 \
    brotli \
    openssl

# Instalar dependências Python
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm" ]; then \
        apk add --no-cache py3-pydantic && pip install --no-cache-dir -r <(grep -v '^pydantic' requirements.txt); \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

RUN apk del .build-deps \
 && rm -rf /root/.cache

# Configure o settings.yml e gere uma secret_key
RUN mkdir -p /etc/searxng && \
    cp ./settings.yml /etc/searxng/settings.yml && \
    chown -R searxng:searxng /etc/searxng && \
    sed -i "s/ultrasecretkey/$(openssl rand -hex 16)/" /etc/searxng/settings.yml && \
    sed -i "s/^  bind_address: .*/  bind_address: \"0.0.0.0\"/" /etc/searxng/settings.yml && \
    sed -i "s/^  port: .*/  port: ${PORT}/" /etc/searxng/settings.yml

RUN su searxng -c "/usr/bin/python3 -m compileall -q searx" \
 && touch -c --date=@0 settings.yml \
 && touch -c --date=@0 dockerfiles/uwsgi.ini \
 && find /usr/local/searxng/searx/static -a \( -name '*.html' -o -name '*.css' -o -name '*.js' \
    -o -name '*.svg' -o -name '*.ttf' -o -name '*.eot' \) \
    -type f -exec gzip -9 -k {} \+ -exec brotli --best {} \+

# Altere para o usuário 'searxng'
USER searxng

# Defina o diretório de trabalho
WORKDIR /usr/local/searxng

# Defina as labels usando as variáveis de ambiente
ARG GIT_URL="https://github.com/lfelipeapo/searxng"
ARG LABEL_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

LABEL maintainer="searxng <${GIT_URL}>" \
      description="A privacy-respecting, hackable metasearch engine." \
      version="${SEARXNG_GIT_VERSION}" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.name="searxng" \
      org.label-schema.version="${SEARXNG_GIT_VERSION}" \
      org.label-schema.url="${GIT_URL}" \
      org.label-schema.vcs-ref=${VERSION_GITCOMMIT} \
      org.label-schema.vcs-url=${GIT_URL} \
      org.label-schema.build-date="${LABEL_DATE}" \
      org.label-schema.usage="https://github.com/searxng/searxng-docker" \
      org.opencontainers.image.title="searxng" \
      org.opencontainers.image.version="${SEARXNG_GIT_VERSION}" \
      org.opencontainers.image.url="${GIT_URL}" \
      org.opencontainers.image.revision=${VERSION_GITCOMMIT} \
      org.opencontainers.image.source=${GIT_URL} \
      org.opencontainers.image.created="${LABEL_DATE}" \
      org.opencontainers.image.documentation="https://github.com/searxng/searxng-docker"
