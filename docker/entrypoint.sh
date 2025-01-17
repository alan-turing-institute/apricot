#! /bin/sh
# shellcheck disable=SC2086
# shellcheck disable=SC2089

# Optional arguments
EXTRA_OPTS=""


# Common server-level options
if [ -z "${PORT}" ]; then
    PORT="1389"
    echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] PORT environment variable is not set: using default of '${PORT}'"
fi

if [ -n "${DEBUG}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --debug"
fi


# LDAP tree arguments
if [ -z "${DOMAIN}" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] DOMAIN environment variable is not set"
    exit 1
fi

if [ -n "${DISABLE_ANONYMOUS_BINDS}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --disable-anonymous-binds"
fi

if [ -n "${DISABLE_MIRRORED_GROUPS}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --disable-mirrored-groups"
fi

if [ -n "${DISABLE_PRIMARY_GROUPS}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --disable-primary-groups"
fi

if [ -n "${DISABLE_USER_DOMAIN_VERIFICATION}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --disable-user-domain-verification"
fi


# OAuth client arguments
if [ -z "${BACKEND}" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] BACKEND environment variable is not set"
    exit 1
fi

if [ -z "${CLIENT_ID}" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] CLIENT_ID environment variable is not set"
    exit 1
fi

if [ -z "${CLIENT_SECRET}" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] CLIENT_SECRET environment variable is not set"
    exit 1
fi


# LDAP refresh arguments
if [ -n "${BACKGROUND_REFRESH}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --background-refresh"
fi

if [ -n "${REFRESH_INTERVAL}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --refresh-interval $REFRESH_INTERVAL"
fi


# Backend arguments: Entra
if [ -n "${ENTRA_TENANT_ID}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --entra-tenant-id $ENTRA_TENANT_ID"
fi


# Backend arguments: Keycloak
if [ -n "${KEYCLOAK_BASE_URL}" ]; then
    if [ -z "${KEYCLOAK_REALM}" ]; then
        echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] KEYCLOAK_REALM environment variable is not set"
        exit 1
    fi
    EXTRA_OPTS="${EXTRA_OPTS} --keycloak-base-url $KEYCLOAK_BASE_URL --keycloak-realm $KEYCLOAK_REALM"
fi
if [ -n "${KEYCLOAK_DOMAIN_ATTRIBUTE}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --keycloak-domain-attribute $KEYCLOAK_DOMAIN_ATTRIBUTE"
fi


# Redis arguments
if [ -n "${REDIS_HOST}" ]; then
    if [ -z "${REDIS_PORT}" ]; then
        REDIS_PORT="6379"
        echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] REDIS_PORT environment variable is not set: using default of '${REDIS_PORT}'"
    fi
    EXTRA_OPTS="${EXTRA_OPTS} --redis-host $REDIS_HOST --redis-port $REDIS_PORT"
fi


# TLS arguments
if [ -n "${TLS_CERTIFICATE}" ] || [ -n "${TLS_PRIVATE_KEY}" ]; then
    # Certificate and key are required
    if [ -z "${TLS_CERTIFICATE}" ]; then
        echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] TLS_CERTIFICATE environment variable is not set"
        exit 1
    fi
    if [ -z "${TLS_PRIVATE_KEY}" ]; then
        echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO    ] TLS_PRIVATE_KEY environment variable is not set"
        exit 1
    fi
    EXTRA_OPTS="${EXTRA_OPTS} --tls-certificate $TLS_CERTIFICATE --tls-private-key $TLS_PRIVATE_KEY"
    # ... but port is optional
    if [ -n "${TLS_PORT}" ]; then
        EXTRA_OPTS="${EXTRA_OPTS} --tls-port $TLS_PORT"
    fi
fi


# Run the server
hatch run python run.py \
    --backend "${BACKEND}" \
    --client-id "${CLIENT_ID}" \
    --client-secret "${CLIENT_SECRET}"  \
    --domain "${DOMAIN}" \
    --port "${PORT}" \
    $EXTRA_OPTS
