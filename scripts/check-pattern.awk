#!/usr/bin/gawk -f

function fatal(output) {
  printf("[FATAL] %s\n", output) >"/dev/stderr";
}

function debug(output) {
  printf("[DEBUG] %s\n", output) >"/dev/stderr";
}

function dump(id, entry,  i, out) {
  # local i    : increment
  # local out  : output string
  out = sprintf("%s:", id);
  for (i = 1; i <= NATTRS; i++)
    out = out sprintf(" %s=<%s>", IATTRS[i], entry[i]);
  printf("%s\n", out) > "/dev/stderr";
}

function isdigit(s) {
  if (DIGITS[s]) return 1;
  return 0;
}

function rewrite(re, a,  new, t) {
  # arg re  : rewrite rule
  # arg a   : array of string to use (return of match())
  # local new   : new string
  # local t     : temporary index
  
  new = "";
  while(length(re) > 1) {
    if (!(t = index(re, "\\"))) break;
    if (t > 1) new = new substr(re, 1, t-1);
    s = substr(re, t+1, 1);
    if (isdigit(s)) {
      new = new a[strtonum(s)];
      re = substr(re, t + 2);
    }
    else {
      new = new "\\" s;
      re = substr(re, t + 2);
    }
  }
  new = new re;
  return new;
}

function notify_nagios(entry) {
  printf("[%lu] PROCESS_SERVICE_CHECK_RESULT:%s:%s:%d:%s\n",
         systime(), entry[HOSTNAME], entry[PROGRAM], 
         entry[NAGIOS_STATE], entry[MSG]) > NAGIOS_EXTERNAL_COMMAND_FILE;
  close(NAGIOS_EXTERNAL_COMMAND_FILE);
}

function rsyslog_ack() {
  print "OK";
  fflush();
}

function cleanup_watchers() {
  # local k   : key
  # local now : current time
  
  # cleanup watch list
  if (length(WATCHERS_TIMEOUT)) {
    now = systime();
    for (k in WATCHERS_TIMEOUT) {
      debug(sprintf("%s: %d < now: %d", k, WATCHERS_TIMEOUT[k], WATCHERS_TIMEOUT[k] < now));
      if (WATCHERS_TIMEOUT[k] < now) {
        # timeout pass, cleanup
        delete WATCHERS_COUNT[k];
        delete WATCHERS_TIMEOUT[k];
      }
    }
  }
}

function config( record, i, iattr, value) {
  # local record  # current record
  # local i       # increment
  # local iattr   # attribut increment
  # value         # current value

  record = 1;
  while (getline <CONFIG && !ERRNO) {
    line++;
    # bypass coments
    if (substr($0, 1, 1) == "#")
      continue;
    
    # empty lines are new sections
    if (NF == 0) {
      # empty line
      if (RULENAMES[record]) {
        record++;
      }
      # initialize (or re-initialize)
      for (i = 1; i <= 8; i++) {
        PATTERNS[record,i] = "";
        REWRITES[record,i] = "";
      }
      FLAGS[record] = 0x0002;
      continue;
    }
    
    # detect & treat keywords
    if (substr($1,1,7) == "PATTERN") {
      if (substr($1,8,1) == ":") {
        iattr = IATTRS[substr($1,9)];
        if (!iattr) {
          fatal(sprintf("%s:%d: bad attr '%s'", CONFIG, line, substr($1,9)));
          exit(1);
        }
      }
      else {
        iattr = MSG;
      }
      value = substr($0, index($0, "\x22")+1);
      value = substr(value, 1, index(value, "\x22")-1);
      PATTERNS[record,iattr] = value;
      # debug(sprintf("PATTERNS[%d,%d] = %s", record, iattr, value));
    }
    else if (substr($1,1,7) == "REWRITE") {
      if (substr($1,8,1) == ":") {
        iattr = IATTRS[substr($1,9)];
        if (!iattr) {
          fatal(sprintf("%s:%d: bad attr '%s'", CONFIG, line, substr($1,9)));
          exit(1);
        }
      }
      else {
        iattr = MSG;
      }
      value = substr($0, index($0, "\x22")+1);
      value = substr(value, 1, index(value, "\x22")-1);
      REWRITES[record,iattr] = value;
      # debug(sprintf("REWRITES[%d,%d] = %s", record, iattr, value));
    }
    else if ($1 == "RULENAME") {
      value = substr($0, index($0, "\x22")+1);
      value = substr(value, 1, index(value, "\x22")-1);
      RULENAMES[record] = value;
    }
    else if ($1 == "THRESHOLD:COUNT") {
      THRESHOLDS_COUNT[record] = $2;
    }
    else if ($1 == "THRESHOLD:TIMEOUT") {
      THRESHOLDS_TIMEOUT[record] = $2;
    }
    else if ($1 == "DISABLE") {
      DISABLED[record] = 1;
    }
    else if ($1 == "CONTINUE") {
      FLAGS[record] = or(and(FLAGS[record],0xfff0),0x0001);
    }
    else if ($1 == "STOP") {
      FLAGS[record] = or(and(FLAGS[record],0xfff0),0x0002);
    }
    else if ($1 == "CRITICAL") {
      FLAGS[record] = or(and(FLAGS[record],0xff0f),0x0010);
    }
    else if ($1 == "WARNING") {
      FLAGS[record] = or(and(FLAGS[record],0xff0f),0x0020);
    }
    else if ($1 == "OK") {
      FLAGS[record] = or(and(FLAGS[record],0xff0f),0x0040);
    }
    else {
      fatal(sprintf("%s,%d: invalid keyword '%s'", CONFIG, line, $1));
    }
    if (!RULENAMES[record])
      RULENAMES[record] = sprintf("#%04d", record);
  }
  if (ERRNO) {
    fatal(sprintf("can't open '%s': %s", CONFIG, ERRNO));
    exit(1);
  }

  # remove potential empty last record
  if (!RULENAMES[record])
    delete RULENAMES[record];
}

function main(line, e, r, ir, a, notify) {
  # local line   : current line
  # local e      : current entry
  # local t      : temporary string
  # local ir     : record increment
  # local ia     : attribut increment
  # local a      : some array
  # local notify : should notify flag

  if (ret < 0) {
    # timeout
    cleanup_watchers();
    return;
  }

  # read record separated by Tabs
  if (!match(line, "^" F F F F F F F "(.*)", e)) {
    rsyslog_ack();
    return;
  }

  # look for known patterns
  for (ir = 1; ir <= length(RULENAMES); ir++) {
    # by pass disabled rules
    if (DISABLED[ir]) continue;

    # need notification ?
    notify = 0;
    
    # loop on each rules attr
    for (ia = 1; ia <= NATTRS; ia++) {
      if (!PATTERNS[ir,ia]) continue;
      debug(sprintf("%s: match(%s,%s,%s) ?", RULENAMES[ir], IATTRS[ia], e[ia], PATTERNS[ir,ia]));
      if (match(e[ia], PATTERNS[ir,ia], a)) {
        # pattern found !
        notify = 1;
        # dump("match", e);
        # FIXME: match others attributes
        if (REWRITES[ir,ia]) {
          t = substr(e[ia], 1, RSTART-1); # empty if LENGTH nul
          t = t rewrite(REWRITES[ir,ia], a);
          t = t substr(e[ia], RSTART + RLENGTH); # empty if START after end
          e[ia] = t;
          # dump("rewrite", e); 
        }
      }
    }
    
    if (notify == 0)
      continue;

    if (THRESHOLDS_COUNT[ir]) {
      # cleanup watchers before adding new ones
      cleanup_watchers();
      # initialize watcher with fixe threshold timeout, default 60sec
      if (!WATCHERS_COUNT[e[HOSTNAME],e[PROGRAM]])
        WATCHERS_TIMEOUT[e[HOSTNAME],e[PROGRAM]] = systime() + \
          (THRESHOLDS_TIMEOUT[ir]?THRESHOLDS_TIMEOUT[ir]:60);
      # increment counter
      WATCHERS_COUNT[e[HOSTNAME],e[PROGRAM]]++;
      # increment task and check for threshold
      if (WATCHERS_COUNT[e[HOSTNAME],e[PROGRAM]] < THRESHOLDS_COUNT[ir])
        notify = 0;
    }
      
    # compute new attrs
    e[NAGIOS_STATE] = NAGIOS_STATES[and(FLAGS[ir],0x00f0)]
    e[RULENAME] = RULENAMES[ir];

    # start actions
    if (notify && DEBUG) {
      dump("notify", e);
    }
    if (notify && NAGIOS_EXTERNAL_COMMAND_FILE) {
      notify_nagios(e);
    }

    # next event
    if (and(FLAGS[ir],0x0002))
      break;
  }

  rsyslog_ack();
  return;
}

BEGIN {
  # read timeout on stding : 1000ms
  PROCINFO["/dev/stdin", "READ_TIMEOUT"] = 1000;
  PROCINFO["/dev/stdin", "RETRY"] = 1;

  IATTRS["TIMEGENERATED"] = TIMEGENERATED = 1;
  IATTRS["TIMEREPORTED"] = TIMEREPORTED = 2;
  IATTRS["FACILITY"] = FACILITY = 3;
  IATTRS["SEVERITY"] = SEVERITY = 4;
  IATTRS["HOSTNAME"] = HOSTNAME = 5;
  IATTRS["HOSTADDR"] = HOSTADDR = 6;
  IATTRS["PROGRAM"] = PROGRAM = 7;
  IATTRS["MSG"] = MSG = 8;
  IATTRS["NAGIOS_STATE"] = NAGIOS_STATE = 9;
  IATTRS["RULENAME"] = RULENAME = 10;
  for (attr in IATTRS) {
    IATTRS[IATTRS[attr]] = attr;
    NATTRS = (NATTRS < IATTRS[attr]) ? IATTRS[attr] : NATTRS;
  }
  
  NAGIOS_STATES[0x0010] = 2; # CRITICAL
  NAGIOS_STATES[0x0020] = 1; # WARNING
  NAGIOS_STATES[0x0040] = 0; # OK
  NAGIOS_STATES[0x0000] = 3; # UNKNOWN
  
  DIGIT_STRING = "0123456789";
  for (i = 1; i < length(DIGIT_STRING); i++)
    DIGITS[substr(DIGIT_STRING, i, 1)] = i;

  # initialize potentialy empty array
  delete RULENAMES;  
  delete WATCHERS_TIMEOUT;
  
  F = "([^\\t]*)\\t"

  if (CONFIG) {
    config();
  }

  if (DEBUG) {
    for (ir = 1; ir <= length(RULENAMES); ir++) {
      debug(sprintf("%s: pattern[msg]=<%s> rewrite[msg]=<%s> flag=0x%04x",
                    RULENAMES[ir],PATTERNS[ir,MSG],REWRITES[ir,MSG],FLAGS[ir]));
    }
  }
  # PATTERNS[1,MSG] = "(..)t";
  # REWRITES[1,MSG] = "\\1toto-\\1-toto";
  # FLAGS[1,CRITICAL] = 1;
  # FLAGS[1,CONTINUE] = 1;

  rsyslog_ack();

  ##########################################
  # main loop
  while (ret = getline line < "/dev/stdin") {
    main(line);
  }
  exit 0;
}

