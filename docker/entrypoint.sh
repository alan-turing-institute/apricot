#! /bin/sh
# shellcheck disable=SC2086
# shellcheck disable=SC2089

# Required arguments
if [ -z "${BACKEND}" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S+0000') [-] BACKEND environment variable is not set"
    exit 1
fi

if [ -z "${CLIENT_ID}" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S+0000') [-] CLIENT_ID environment variable is not set"
    exit 1
fi

if [ -z "${CLIENT_SECRET}" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S+0000') [-] CLIENT_SECRET environment variable is not set"
    exit 1
fi

if [ -z "${DOMAIN}" ]; then
    echo "$(date +'%Y-%m-%d %H:%M:%S+0000') [-] DOMAIN environment variable is not set"
    exit 1
fi

# Arguments with defaults
if [ -z "${PORT}" ]; then
    PORT="1389"
    echo "$(date +'%Y-%m-%d %H:%M:%S+0000') [-] PORT environment variable is not set: using default of '${PORT}'"
fi



# Optional arguments
EXTRA_OPTS=""
if [ -n "${DEBUG}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --debug"
fi

if [ -n "${DISABLE_GROUP_OF_GROUPS}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --disable-group-of-groups"
fi

if [ -n "${ENTRA_TENANT_ID}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --entra-tenant-id $ENTRA_TENANT_ID"
fi

if [ -n "${REDIS_HOST}" ]; then
    if [ -z "${REDIS_PORT}" ]; then
        REDIS_PORT="6379"
        echo "$(date +'%Y-%m-%d %H:%M:%S+0000') [-] REDIS_PORT environment variable is not set: using default of '${REDIS_PORT}'"
    fi
    EXTRA_OPTS="${EXTRA_OPTS} --redis-host $REDIS_HOST --redis-port $REDIS_PORT"
fi

if [ -n "${KEYCLOAK_BASE_URL}" ]; then
    if [ -z "${KEYCLOAK_REALM}" ]; then
        echo "$(date +'%Y-%m-%d %H:%M:%S+0000') [-] KEYCLOAK_REALM environment variable is not set"
        exit 1
    fi
    EXTRA_OPTS="${EXTRA_OPTS} --keycloak-base-url $KEYCLOAK_BASE_URL --keycloak-realm $KEYCLOAK_REALM"
fi

# Run the server
hatch run python run.py \
    --backend "${BACKEND}" \
    --client-id "${CLIENT_ID}" \
    --client-secret "${CLIENT_SECRET}"  \
    --domain "${DOMAIN}" \
    --port "${PORT}" \
    $EXTRA_OPTS
