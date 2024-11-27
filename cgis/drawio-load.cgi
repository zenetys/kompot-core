#!/bin/bash

DATADIR=${DRAWIO_DATADIR:-/var/www/html}

function header() {
    printf '%s\r\n' "$*"
}

schema_name=${SCRIPT_URL##*/}
schema_name=${schema_name//[^[:alnum:]+_.-]/_}

if [[ ! -r $DATADIR/$schema_name.xml ]]; then
  header 'Status: 404'
  header "X-Error: $schema_name not found"
  header ''
  exit 1
fi

header 'Status: 200'
header 'Content-Type: text/xml; charset=UTF-8'
header ''

cat "$DATADIR/$schema_name.xml"
