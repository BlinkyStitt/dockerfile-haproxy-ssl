# TODO: this image could be smaller, but i don't care too much about that right now

FROM haproxy:alpine
# plus parts of https://hub.docker.com/r/certbot/certbot/~/dockerfile/
# plus acme plugin for haproxy
# plus our script for automatic certificate creation and renewal
# plus (a work in progress) sqrl plugin for haproxy

# openssl is actually for generating dh_params. something smaller might be able to do that instead
RUN apk add --no-cache --virtual .certbot-deps \
    curl \
    libffi \
    libssl1.0 \
    ca-certificates \
    binutils \
    openssl \
    python2 \
    py2-pip

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    libffi-dev \
    linux-headers \
    musl-dev \
    openssl-dev \
    python2-dev \
 && mkdir -p /opt/ \
 && curl -L https://github.com/certbot/certbot/archive/master.tar.gz | tar xvz -C /opt/ \
 && pip install --no-cache-dir \
    --editable /opt/certbot-master/acme/ \
    --editable /opt/certbot-master/ \
 && apk del .build-deps

VOLUME /etc/letsencrypt /var/lib/letsencrypt

# certificate helpers
COPY acme-http01-webroot.lua /usr/local/etc/haproxy/
COPY certbot-haproxy.py /usr/local/sbin/

# sqrl authentication plugin (work in progress)
COPY sqrl.lua /usr/local/etc/haproxy/

COPY haproxy.cfg /usr/local/etc/haproxy/
COPY domain2backend.map /usr/local/etc/haproxy/
