#!/bin/sh
# Run the real entrypoint against an offline hatch stub, with no OAuth access.
set -eu
ENTRYPOINT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/entrypoint.sh"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT HUP INT TERM
cat > "$WORKDIR/hatch" <<'STUB'
#!/bin/sh
printf '%s\n' "$@" > "$CAPTURED_ARGS"
STUB
chmod +x "$WORKDIR/hatch"
export PATH="$WORKDIR:$PATH" CAPTURED_ARGS="$WORKDIR/arguments"
export BACKEND=MicrosoftEntra CLIENT_ID=abc123 DOMAIN=example.org ENTRA_TENANT_ID=tenant-id
for secret in '-starting-with-dash' '--client-id=looks-like-option' '-with spaces & symbols'; do
  CLIENT_SECRET="$secret" sh "$ENTRYPOINT"
  # The equal-sign syntax must produce one token even for leading dashes,
  # and must preserve embedded spaces and shell metacharacters.
  grep -Fx -- "--client-secret=$secret" "$CAPTURED_ARGS" > /dev/null
  test "$(grep -Fc -- '--client-secret=' "$CAPTURED_ARGS")" -eq 1
  grep -Fx -- 'tenant-id' "$CAPTURED_ARGS" > /dev/null
done
if CLIENT_SECRET='' sh "$ENTRYPOINT" > "$WORKDIR/missing.log" 2>&1; then
  echo 'Empty client secrets must still be rejected.' >&2
  exit 1
fi
grep -F 'CLIENT_SECRET environment variable is not set' "$WORKDIR/missing.log" > /dev/null
echo 'Apricot entrypoint argument tests: PASS'
