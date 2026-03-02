#!/bin/bash
##
## Simple CGI library to be defined as shebang
## Copyright 2020 - Zenetys
## License: MIT

## Source :
## 	wget -nv "https://github.com/zenetys/ztools/raw/dev/bdo/cgi/cgi/lib.cgi"

function debug() {
  echo "$*" "$*" >&2
}

function header() {
  local header=$1 ; shift

  if [[ $HEADERS_SENT != 1 ]]; then
    if [[ $header && "$header" != "--send" ]]; then
      echo -e "$header\r"
    else
      echo -e "\r"
      HEADERS_SENT=1
    fi
  fi
}

function html_page() {
  local title=$1; shift
  local body=$1; shift
  header "Content-Type: text/html"
  header --send
  echo -n "<html><head><title>$title</title></head>"
  echo -n "<body><h1>$title</h1><p>$body</p></body>"
  echo -n "</html>"
  echo
}

function fatal() {
  local msg="$1"; shift
  local msg2=${1:-$msg}; shift

  printf "[FATAL] %s" "$msg2" >&2
  if (( HEADERS_SENT == 1 )); then
    printf "<!-- X-Error: %s -->" "$msg"
  else
    header "Status: 500"
    header "X-Error: $msg"
    header --send
    html_page "ERROR 500" "FATAL: $msg"
  fi
  exit 1
}

function show_debug_info() {
  local vars=(
    SCRIPT
    NOW
    PWD
    UID EUID
    HOSTNAME
    CONTENT_LENGTH
    CONTENT_TYPE
    CONTEXT_DOCUMENT_ROOT
    CONTEXT_PREFIX
    DOCUMENT_ROOT
    GATEWAY_INTERFACE
    QUERY_STRING
    REQUEST_{METHOD,SCHEME,URI}
    SCRIPT_FILENAME
    SCRIPT_NAME
    ${!ENV_*}
    ${!SERVER_*}
    ${!REMOTE_*}
    ${!HTTP_*}
    ${!SSL_*}
    ${!_GET_*}
    ${!_POST_*}
    ${!_COOKIE_*}
    ${!_TEMP_*}
  )
  local var next

  (( HTTP_X_DEBUG >= 3 )) && ( set -o posix ; set ) && return

  header --send
  for var in ${vars[@]} ; do
    eval -- "[[ \${${var}:60:1} ]] && next='...' || next=''"
    eval -- echo "$var=\"\${${var}:0:60}$next\""
  done
}

function url_decode() {
  url_decode=1 var_decode "$@"
}

function var_decode() {
  local prefix="$1" ; shift
  local url_decode=${url_decode:-0}
  local sub var val

  for sub in $*; do
    [[ $sub ]] || continue
    var=${sub%%=*}             # get variable name
    var=${var//[^[:alnum:]]/_} # replace non alnum by '_'
    val=${sub#*=}              # get value
    if (( url_decode == 1 )); then
      val=${val//+/\\x20}        # replace '+' with <SP>
      val=${val//%/\\x}          # replace '%' with \\x (%XX => \xXX)
      val=${val//\\x\\x/%}       # replace \\x\\x (initial double '%') with '%'
    fi
    eval "$prefix${var}=\$'${val}'"
  done
}

# Parse period parameter and set PERIOD_SINCE and PERIOD_BEFORE (unix timestamps)
# Usage: parse_period "$period" && SINCE=$PERIOD_SINCE && BEFORE=$PERIOD_BEFORE
# Returns 0 if period was recognized, 1 otherwise
# Supported periods:
#   last-1h, last-6h, last-12h, last-24h    - last N hours
#   last-7d, last-30d, last-90d, last-365d  - last N days
#   today, yesterday                         - current/previous day (midnight to midnight)
#   this-week, last-week                     - current/previous week (Monday-based)
#   this-month, last-month                   - current/previous month
#   this-year, last-year                     - current/previous year
function parse_period() {
  local period=$1
  local now=${NOW:-$(date +%s)}

  # Get current date components in UTC
  local today_midnight=$(date -u -d "$(date -u -d @$now +%Y-%m-%d)" +%s)
  local year=$(date -u -d @$now +%Y)
  local month=$(date -u -d @$now +%m)
  local dow=$(date -u -d @$now +%u)  # 1=Monday, 7=Sunday

  case $period in
    # Rolling windows
    last-1h)
      PERIOD_SINCE=$(( now - 3600 ))
      PERIOD_BEFORE=$now
      ;;
    last-6h)
      PERIOD_SINCE=$(( now - 6 * 3600 ))
      PERIOD_BEFORE=$now
      ;;
    last-12h)
      PERIOD_SINCE=$(( now - 12 * 3600 ))
      PERIOD_BEFORE=$now
      ;;
    last-24h)
      PERIOD_SINCE=$(( now - 24 * 3600 ))
      PERIOD_BEFORE=$now
      ;;
    last-7d)
      PERIOD_SINCE=$(( now - 7 * 86400 ))
      PERIOD_BEFORE=$now
      ;;
    last-30d)
      PERIOD_SINCE=$(( now - 30 * 86400 ))
      PERIOD_BEFORE=$now
      ;;
    last-90d)
      PERIOD_SINCE=$(( now - 90 * 86400 ))
      PERIOD_BEFORE=$now
      ;;
    last-365d)
      PERIOD_SINCE=$(( now - 365 * 86400 ))
      PERIOD_BEFORE=$now
      ;;

    # Calendar periods
    today)
      PERIOD_SINCE=$today_midnight
      PERIOD_BEFORE=$now
      ;;
    yesterday)
      PERIOD_SINCE=$(( today_midnight - 86400 ))
      PERIOD_BEFORE=$today_midnight
      ;;
    last-2d)
      PERIOD_SINCE=$(( today_midnight - 2 * 86400 ))
      PERIOD_BEFORE=$today_midnight
      ;;
    this-week)
      # Monday of current week
      PERIOD_SINCE=$(( today_midnight - (dow - 1) * 86400 ))
      PERIOD_BEFORE=$now
      ;;
    last-week)
      # Previous week Monday to Sunday
      local this_monday=$(( today_midnight - (dow - 1) * 86400 ))
      PERIOD_SINCE=$(( this_monday - 7 * 86400 ))
      PERIOD_BEFORE=$this_monday
      ;;
    this-month)
      PERIOD_SINCE=$(date -u -d "$year-$month-01" +%s)
      PERIOD_BEFORE=$now
      ;;
    last-month)
      if (( month == 1 )); then
        PERIOD_SINCE=$(date -u -d "$(( year - 1 ))-12-01" +%s)
        PERIOD_BEFORE=$(date -u -d "$year-01-01" +%s)
      else
        PERIOD_SINCE=$(date -u -d "$year-$(printf %02d $((month - 1)))-01" +%s)
        PERIOD_BEFORE=$(date -u -d "$year-$month-01" +%s)
      fi
      ;;
    this-year)
      PERIOD_SINCE=$(date -u -d "$year-01-01" +%s)
      PERIOD_BEFORE=$now
      ;;
    last-year)
      PERIOD_SINCE=$(date -u -d "$(( year - 1 ))-01-01" +%s)
      PERIOD_BEFORE=$(date -u -d "$year-01-01" +%s)
      ;;
    *)
      return 1
      ;;
  esac
  return 0
}

function on_exit() {
  [[ $_TEMP_CONTENT_DATA ]] && rm -f $_TEMP_CONTENT_DATA
  if (( HEADERS_SENT != 1 )); then
    header "Status: 500"
    header "X-Error: no data"
    header --send
  fi
}

trap on_exit EXIT

[[ ${HTTP_X_DEBUG} -ge 2 ]] && set -x

declare NOW=$(date +%s)
declare SCRIPT="$1"; shift

if [[ ${QUERY_STRING} ]]; then
  IFS='&' url_decode _GET_ "$QUERY_STRING"
fi

if [[ ${CONTENT_TYPE} == application/x-www-form-urlencoded ]] &&
   [[ ${CONTENT_LENGTH} ]]; then
  if (( ${CONTENT_LENGTH} < 8192 )); then
    IFS='&' url_decode _${REQUEST_METHOD}_ "$(cat)"
  else
    # do not parse too long POST
    declare _TEMP_CONTENT_DATA=$(mktemp)
    cat > $_TEMP_CONTENT_DATA
  fi
elif [[ ${CONTENT_LENGTH} ]] && (( $CONTENT_LENGTH > 0 )); then
  # do not parse too long POST
  declare _TEMP_CONTENT_DATA=$(mktemp)
  cat > $_TEMP_CONTENT_DATA
fi

if [[ ${HTTP_COOKIE} ]]; then
  IFS='; ' var_decode _COOKIE_ "${HTTP_COOKIE}"
fi

[[ ${HTTP_X_DEBUG} -ge 1 ]] && show_debug_info 2>/dev/null

if [[ ${SCRIPT} ]]; then
    source "${SCRIPT}"
fi

