FROM alpine:3.20

# Instale o libcap, o Git, o Python e outras dependências de compilação
RUN apk add --no-cache libcap git python3 py3-pip py3-virtualenv build-base linux-headers python3-dev

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
    PORT=8080 \
    VENV_PATH=/usr/local/searxng/venv

WORKDIR /usr/local/searxng

# Crie o ambiente virtual
RUN python3 -m venv $VENV_PATH && \
    $VENV_PATH/bin/pip install --upgrade pip

# Copie os arquivos do projeto
COPY . .

# Instalar dependências do Python no ambiente virtual
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm" ]; then \
        apk add --no-cache py3-pydantic && \
        $VENV_PATH/bin/pip install --no-cache-dir -r <(grep -v '^pydantic' requirements.txt); \
    else \
        $VENV_PATH/bin/pip install --no-cache-dir -r requirements.txt; \
    fi

# Remova pacotes de compilação após a instalação das dependências
RUN apk del build-base linux-headers python3-dev gcc musl-dev \
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
