#!/bin/bash

# set -x

function header() {
  printf "%s\r\n" "$*"
}

DATADIR="${DRAWIO_DATADIR:-/var/www/html}"

# get query string parameters (explicit allow-list, never let the client
# override arbitrary shell variables such as DATADIR)
url=""
base64=0
IFS='&' read -ra _params <<< "$QUERY_STRING"
for _kv in "${_params[@]}"; do
  case ${_kv%%=*} in
    url)    url=${_kv#*=} ;;
    base64) base64=${_kv#*=} ;;
  esac
done

# protect url
url=${url//[^[:alnum:]+_.-]/_}

# defense in depth: the resolved file must stay under DATADIR
_realfile=$(realpath -m -- "$DATADIR/$url.xml")
case $_realfile in
  "$DATADIR"/*) ;;
  *)
    header "Status: 400"
    header "X-Error: invalid url"
    header ""
    exit 1
    ;;
esac

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

