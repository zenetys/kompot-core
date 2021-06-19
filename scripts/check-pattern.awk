#!/usr/bin/awk -f

function fatal(output) {
  printf("[FATAL] %s\n", output) >"/dev/stderr";
}

function debug(output) {
  printf("[DEBUG] %s\n", output) >"/dev/stderr";
}

BEGIN {
  NAGIOS_COMMAND_FILE = "/dev/stderr";

  IATTRS["TIMEGENERATED"] = TIMEGENERATED = 1;
  IATTRS["TIMEREPORTED"] = TIMEREPORTED = 2;
  IATTRS["FACILITY"] = FACILITY = 3;
  IATTRS["SEVERITY"] = SEVERITY = 4;
  IATTRS["HOSTNAME"] = HOSTNAME = 5;
  IATTRS["HOSTADDR"] = HOSTADDR = 6;
  IATTRS["PROGRAM"] = PROGRAM = 7;
  IATTRS["MSG"] = MSG = 8;
  
  NAGIOS_STATE[0x0010] = 2; # CRITICAL
  NAGIOS_STATE[0x0020] = 1; # WARNING
  NAGIOS_STATE[0x0040] = 0; # OK
  NAGIOS_STATE[0x0000] = 3; # UNKNOWN
  
  F = "([^\\t]*)\\t"

  if (CONFIG) {
    record = 1;
    while (getline <CONFIG && !ERRNO) {
      line++;
      if (NF == 0) {
        # empty line
        if (PATTERNS[record,IATTRS["MSG"]]) {
          record++;
        }
        # initialize (or re-initialize)
        for (i = 1; i <= 8; i++) {
          PATTERNS[record,i] = "";
          REWRITES[record,i] = "";
        }
        FLAGS[record] = 0x0002;
      }
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
    }
    if (ERRNO) {
      fatal(sprintf("can't open '%s': %s", CONFIG, ERRNO));
      exit(1);
    }
  }
  # remove potential empty last record
  if (!PATTERNS[record,MSG]) record--;

  for (r = 1; r <= record; r++) {
    debug(sprintf("#%d: pattern[msg]=<%s> rewrite[msg]=<%s> flag=0x%04x",
                  r,PATTERNS[r,MSG],REWRITES[r,MSG],FLAGS[r]));
  }
  # PATTERNS[1,MSG] = "(..)t";
  # REWRITES[1,MSG] = "\\1toto-\\1-toto";
  # FLAGS[1,CRITICAL] = 1;
  # FLAGS[1,CONTINUE] = 1;

  print "OK";
  fflush();
}

function dump(id,f) {
  printf("%s: <%s> <%s> <%s> <%s> <%s> <%s> <%s> <%s>\n", id, 
         f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]) > "/dev/stderr";
}

function rewrite(origin, re, array, new, t, i) {
  while(length(re) > 0) {
    if (!(t = index(re, "\\"))) break;
    if (t > 1) new = new substr(re, 1, t-1);
    i = strtonum(substr(re, t+1, 1));
    new = new array[i];
    re = substr(re, t + 2);
  }
  new = new re;
  return new;
}

function notify_nagios(state, entry) {
  printf("[%lu] PROCESS_SERVICE_CHECK_RESULT:%s:%s:%d:%s\n",
         systime(), entry[HOSTNAME], entry[PROGRAM], state, entry[MSG]) \
         > NAGIOS_COMMAND_FILE;
}

{
  # read record separated by Tabs
  if (!match($0, "^" F F F F F F F "(.*)", e))
    next;
 
  # look for known patterns
  for (i = 1; i <= 1; i++) {
    if (match(e[MSG], PATTERNS[i,MSG], a)) {
      # dump("match", e);
      # FIXME: match others attributes
      if (REWRITES[i,MSG]) {
        e[MSG] = rewrite(e[MSG], REWRITES[i,MSG], a);
        # dump("rewrite", e); 
      }
      
      notify_nagios(NAGIOS_STATE[and(FLAGS[i],0x00f0)], e);

      if (and(FLAGS[i],0x0002))
        break;
    }
  }
  print "OK";
  fflush();
}
