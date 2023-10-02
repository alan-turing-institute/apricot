#! /bin/sh
# shellcheck disable=SC2086
# shellcheck disable=SC2089

if [ -z "${BACKEND}" ]; then
    echo "BACKEND environment variable is not set"
    exit 1
fi

if [ -z "${CLIENT_ID}" ]; then
    echo "CLIENT_ID environment variable is not set"
    exit 1
fi

if [ -z "${CLIENT_SECRET}" ]; then
    echo "CLIENT_SECRET environment variable is not set"
    exit 1
fi

if [ -z "${DOMAIN}" ]; then
    echo "DOMAIN environment variable is not set"
    exit 1
fi

# Optional arguments
EXTRA_OPTS=""
if [ -n "${ENTRA_TENANT_ID}" ]; then
    EXTRA_OPTS="${EXTRA_OPTS} --entra-tenant-id $ENTRA_TENANT_ID"
fi

# Run the server
hatch run python run.py \
    --backend "$BACKEND" \
    --client-id "$CLIENT_ID" \
    --client-secret "$CLIENT_SECRET"  \
    --domain "$DOMAIN" \
    --port 1389 \
    $EXTRA_OPTS
