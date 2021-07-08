#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PGDATABASE="experiment_data" \
PGUSER="$(cat $SCRIPT_DIR/database/secrets/postgres-user.secret)" \
PGPASS="$(cat $SCRIPT_DIR/database/secrets/postgres-password.secret)" \
GDRIVE_CREDENTIALS="$SCRIPT_DIR/secrets/gdrive-credentials.json" \
GDRIVE_TOKEN="$SCRIPT_DIR/secrets/gdrive-token.json" \
"$@"