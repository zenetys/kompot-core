#!/bin/bash

# set -x

function header() {
  printf "%s\r\n" "$*"
}

DATADIR="${DRAWIO_DATADIR:-/var/www/html}"

# get query string parameters
declare ${QUERY_STRING//&/$IFS}

# protect url
url=${url//[^[:alnum:]+_.-]/_}

if [[ ! -r $DATADIR/$url.xml ]]; then
  header "Status: 400"
  header "X-Error: $url not found"
  header ""
  exit 1
fi

header "Status: 200"
header "Content-Type: text/xml; charset=UTF-8"
header ""

if [[ $base64 == 1 ]]; then
  cat $DATADIR/$url.xml | base64 -w 0
else
  cat $DATADIR/$url.xml
fi

