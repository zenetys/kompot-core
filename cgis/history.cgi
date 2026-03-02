#!/usr/bin/env ./lib.cgi
#
# history.cgi - Query nagios history from SQLite database
#
# Parameters:
#   action   - Tables to query (comma-separated): state, notification, external, system
#   hostname - Filter by hostname (exact match)
#   service  - Filter by service (exact match)
#   state    - Filter by state (exact match or comma-separated)
#   since    - Minimum timestamp (unix epoch, inclusive)
#   before   - Maximum timestamp (unix epoch, exclusive)
#   period   - Preset time range (overrides since/before): last-24h, yesterday, this-week, etc.
#   query    - Unified filter syntax: "value" (search all) or "field:value" (exact match)
#   limit    - Max results (default 500)
#   hostonly - 1 = hosts only (service IS NULL)
#   initial  - 0 = exclude initial states
#

source ./filter.cgi

HISTORY_DB=${KOMPOT_HISTORY_DB:-/var/lib/kompot/nagios/nagios-history.db}

[[ -r $HISTORY_DB ]] ||
  fatal "database not found: $HISTORY_DB"

# --- Parse parameters ---

ACTION=${_GET_action//[^a-zA-Z,]}
LIMIT=${_GET_limit//[^0-9]}
LIMIT=${LIMIT:-500}
HOSTONLY=${_GET_hostonly//[^01]}
INITIAL=${_GET_initial//[^01]}
PERIOD=${_GET_period//[^a-z0-9-]}

# Parse unified query (supports: "value", "field:value", "field:~value", "-field:value")
filter_parse "${_GET_query//[^a-zA-Z0-9._:/ @#!,+-]}"

# Legacy individual parameters → append as filter terms
HOSTNAME=${_GET_hostname//[^a-zA-Z0-9._-]}
SERVICE=${_GET_service//[^a-zA-Z0-9._:/ -]}
STATE=${_GET_state//[^a-zA-Z_,]}
[[ $HOSTNAME ]] && filter_add "hostname:$HOSTNAME"
[[ $SERVICE ]]  && filter_add "service:$SERVICE"
[[ $STATE ]]    && filter_add "state:$STATE"

# Time range
SINCE=${_GET_since//[^0-9]}
BEFORE=${_GET_before//[^0-9]}
if [[ $PERIOD ]]; then
  if parse_period "$PERIOD"; then
    SINCE=$PERIOD_SINCE
    BEFORE=$PERIOD_BEFORE
  else
    fatal "invalid period '$PERIOD'"
  fi
fi
filter_add_time_range "$SINCE" "$BEFORE" timestamp

# --- Table-specific configuration ---

# Fields to search when query has no field prefix (e.g. "SRV-01")
declare -A TABLE_SEARCH_FIELDS=(
  [state]="hostname service output"
  [notification]="hostname service contact output"
  [external]="hostname service command data"
  [system]="event data"
)

# Valid fields for field:value filters (fields not in the list are skipped for that table)
declare -A TABLE_VALID_FIELDS=(
  [state]="hostname service state state_type"
  [notification]="hostname service state contact"
  [external]="hostname service command"
  [system]="event"
)

# --- Query building ---

# Build WHERE clause for a table using the filter library
function build_where() {
  local table=$1

  # Configure searchable fields for this table
  FILTER_SEARCHABLE_FIELDS=${TABLE_SEARCH_FIELDS[$table]}

  # Generate SQL clauses (with field whitelist for this table)
  filter_to_sql_clauses "${TABLE_VALID_FIELDS[$table]}"

  # Table-specific extra clauses
  case $table in
    state|notification|external)
      [[ $HOSTONLY == 1 ]] && FILTER_SQL_CLAUSES+=( "service IS NULL" )
      ;;
  esac
  case $table in
    state)
      [[ $INITIAL == 0 ]] && FILTER_SQL_CLAUSES+=( "attempt IS NOT NULL" )
      ;;
  esac

  filter_sql_where
}

# Build a SELECT for a single table with normalized columns for UNION ALL
function build_select() {
  local table=$1
  local where=$(build_where "$table")

  case $table in
    state)
      echo "SELECT 'state' AS _type, hostname, service, state, state_type, attempt, NULL AS contact, NULL AS command, output, NULL AS event, NULL AS data, timestamp FROM state $where"
      ;;
    notification)
      echo "SELECT 'notification' AS _type, hostname, service, state, NULL AS state_type, NULL AS attempt, contact, command, output, NULL AS event, NULL AS data, timestamp FROM notification $where"
      ;;
    external)
      echo "SELECT 'external' AS _type, hostname, service, NULL AS state, NULL AS state_type, NULL AS attempt, NULL AS contact, command, NULL AS output, NULL AS event, data, timestamp FROM external $where"
      ;;
    system)
      echo "SELECT 'system' AS _type, NULL AS hostname, NULL AS service, NULL AS state, NULL AS state_type, NULL AS attempt, NULL AS contact, NULL AS command, NULL AS output, event, data, timestamp FROM system $where"
      ;;
  esac
}

# Single table query (original behavior, no _type column)
function query_single() {
  local table=$1
  local where=$(build_where "$table")
  sqlite3 -json "$HISTORY_DB" \
    "SELECT * FROM $table $where ORDER BY timestamp DESC LIMIT $LIMIT;"
}

# Multi-table query with UNION ALL
function query_multi() {
  local tables=("$@")
  local sql=""
  local t

  for t in "${tables[@]}"; do
    [[ $sql ]] && sql+=" UNION ALL "
    sql+="$(build_select "$t")"
  done

  sql+=" ORDER BY timestamp DESC LIMIT $LIMIT;"

  sqlite3 -json "$HISTORY_DB" "$sql"
}

# --- Determine which tables to query ---

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

# --- Execute and output ---

header "Status: 200"
header "Content-Type: application/json"
header --send

if (( ${#TABLES[@]} == 1 )); then
  query_single "${TABLES[0]}"
else
  query_multi "${TABLES[@]}"
fi
