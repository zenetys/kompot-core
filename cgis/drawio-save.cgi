#!/bin/bash

DATADIR=${DRAWIO_DATADIR:-/var/www/html}
TMPDIR=${TMPDIR:-/dev/shm}

function header() {
    printf '%s\r\n' "$*"
}

function on_exit() {
    if (( STATUS == 0 )); then
        header 'Status: 200'
    else
        header 'Status: 500'
    fi
    header ''
    [[ -e $TMPFILE ]] && rm -f "$TMPFILE"
    return 0
}

STATUS=-1
TMPFILE="$TMPDIR/${schema_name}.${RANDOM}${RANDOM}.drawio"
trap on_exit EXIT

schema_name=${SCRIPT_URL##*/}
schema_name=${schema_name//[^[:alnum:]+_.-]/_}

set -e
cat > "$TMPFILE"
mv -f "$TMPFILE" "$DATADIR/$schema_name.xml"
STATUS=$?
