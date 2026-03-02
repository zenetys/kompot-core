#!/usr/bin/env ./lib.cgi
#
# history-stats.cgi - Aggregate nagios history events by time period
#
# Parameters:
#   granularity - Aggregation period: hour, day (default), week, month
#   days        - Number of days to cover (default: 365)
#   before      - Unix timestamp end (default: now)
#   period      - Preset time range (overrides days/before): last-24h, yesterday, this-week, etc.
#   action      - Filter by type(s): state,notification,external,system
#   state       - Filter by state(s): OK,WARNING,CRITICAL,UNKNOWN
#   hostonly    - 1 = hosts only (service empty)
#   query       - Free text search (hostname, service)
#

HISTORY_DB=${KOMPOT_HISTORY_DB:-/var/lib/kompot/nagios/nagios-history.db}

[[ -r $HISTORY_DB ]] ||
  fatal "database not found: $HISTORY_DB"

GRANULARITY=${_GET_granularity//[^a-z]}
GRANULARITY=${GRANULARITY:-day}
DAYS=${_GET_days//[^0-9]}
DAYS=${DAYS:-365}
BEFORE=${_GET_before//[^0-9]}
BEFORE=${BEFORE:-$NOW}
ACTION=${_GET_action//[^a-zA-Z,]}
STATE=${_GET_state//[^a-zA-Z_,]}
HOSTONLY=${_GET_hostonly//[^01]}
INITIAL=${_GET_initial//[^01]}
QUERY=${_GET_query//[^a-zA-Z0-9._:/ @#!+-]}
PERIOD=${_GET_period//[^a-z0-9-]}

# Validate granularity
case $GRANULARITY in
  hour|day|week|month) ;;
  *) fatal "invalid granularity '$GRANULARITY'" ;;
esac

# Calculate time range
if [[ $PERIOD ]]; then
  if parse_period "$PERIOD"; then
    SINCE=$PERIOD_SINCE
    BEFORE=$PERIOD_BEFORE
  else
    fatal "invalid period '$PERIOD'"
  fi
else
  SINCE=$(( BEFORE - DAYS * 86400 ))
fi

# Timestamp column name (same for all tables)
TS_COL=timestamp

# Build date grouping expression based on granularity
function date_expr() {
  case $GRANULARITY in
    hour)
      echo "strftime('%Y-%m-%d %H:00', $TS_COL)"
      ;;
    day)
      echo "date($TS_COL)"
      ;;
    week)
      # ISO week: Monday-based week
      echo "strftime('%Y-W%W', $TS_COL)"
      ;;
    month)
      echo "strftime('%Y-%m', $TS_COL)"
      ;;
  esac
}

# Build WHERE clause for a table
function build_where() {
  local table=$1
  local clauses=()

  # Time range (always applied)
  clauses+=( "$TS_COL >= datetime($SINCE, 'unixepoch')" )
  clauses+=( "$TS_COL < datetime($BEFORE, 'unixepoch')" )

  case $table in
    state|notification|external)
      [[ $HOSTONLY == 1 ]] && clauses+=( "service IS NULL" )
      ;;
  esac

  case $table in
    state)
      [[ $INITIAL == 0 ]] && clauses+=( "attempt IS NOT NULL" )
      ;;
  esac

  case $table in
    state|notification)
      if [[ $STATE ]]; then
        if [[ $STATE == *,* ]]; then
          local in_list="'${STATE//,/\',\'}'"
          clauses+=( "state IN ($in_list)" )
        else
          clauses+=( "state = '$STATE'" )
        fi
      fi
      ;;
  esac

  if [[ $QUERY ]]; then
    local like="'%${QUERY//\'/\'\'}%'"
    case $table in
      state)
        clauses+=( "(hostname LIKE $like OR service LIKE $like)" )
        ;;
      notification)
        clauses+=( "(hostname LIKE $like OR service LIKE $like)" )
        ;;
      external)
        clauses+=( "(hostname LIKE $like OR service LIKE $like)" )
        ;;
      system)
        clauses+=( "(event LIKE $like OR data LIKE $like)" )
        ;;
    esac
  fi

  if (( ${#clauses[@]} > 0 )); then
    local old_ifs=$IFS
    IFS=$'\x1f'
    local result="${clauses[*]}"
    IFS=$old_ifs
    echo "WHERE ${result//$'\x1f'/ AND }"
  fi
}

# Build SELECT for aggregation from a single table
function build_agg_select() {
  local table=$1
  local where=$(build_where "$table")
  local dexpr=$(date_expr "$table")

  echo "SELECT $dexpr AS date, COUNT(*) AS count FROM $table $where GROUP BY date"
}

# Determine which tables to query
VALID_ACTIONS=(state notification external system)
TABLES=()

if [[ $ACTION ]]; then
  IFS=',' read -ra ACTIONS <<< "$ACTION"
  for a in "${ACTIONS[@]}"; do
    found=0
    for v in "${VALID_ACTIONS[@]}"; do
      if [[ $a == "$v" ]]; then
        found=1
        break
      fi
    done
    (( found )) || fatal "unknown action '$a'"
    TABLES+=( "$a" )
  done
else
  # Default: all tables
  TABLES=("${VALID_ACTIONS[@]}")
fi

# Build the aggregation query
if (( ${#TABLES[@]} == 1 )); then
  SQL="$(build_agg_select "${TABLES[0]}") ORDER BY date DESC;"
else
  # Union all tables then aggregate
  SQL="SELECT date, SUM(count) AS count FROM ("
  first=1
  for t in "${TABLES[@]}"; do
    (( first )) || SQL+=" UNION ALL "
    SQL+="$(build_agg_select "$t")"
    first=0
  done
  SQL+=") GROUP BY date ORDER BY date DESC;"
fi

# Execute query and build JSON response
DATA=$(sqlite3 -json "$HISTORY_DB" "$SQL")

# Calculate from/to dates for response
FROM_DATE=$(date -u -d "@$SINCE" +%Y-%m-%d)
TO_DATE=$(date -u -d "@$BEFORE" +%Y-%m-%d)

header "Status: 200"
header "Content-Type: application/json"
header --send

# Build final JSON response
cat <<EOF
{
  "granularity": "$GRANULARITY",
  "from": "$FROM_DATE",
  "to": "$TO_DATE",
  "data": $DATA
}
EOF
