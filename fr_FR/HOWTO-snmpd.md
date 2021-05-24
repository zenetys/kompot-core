# Configuration de l'agent Net-SNMP Linux & Windows

## 1. Prérequis

Pour l'ensemble des systèmes, il faut déterminer des comptes SNMPv3:

  * pour les communications avec l'agent interne (`internal`)
  * pour les requêtes SNMP depuis un serveur vers l'agent (`monitor`)
  * pour l'émission de trap vers un serveur (`trap`)

### 1.1. Debian

* <code>snmpd</code>, et ses dépendances
 * <code>libsnmp-base</code>
 * <code>libsnmp-perl</code>
 * <code>libsnmp30:amd64</code>

### 1.2. Redhat

* <code>net-snmp</code>, et ses dépendances
 * <code>net-snmp-agent-libs</code>
 * <code>net-snmp-libs</code>

### 1.3. Windows

FIXME

## 2. Modèle de configuration

``` sh
## Filename: snmpd-local.template
## License: MIT (2021)
## Description: template for /etc/snmp/snmpd-local.conf

## enable feature agent-X (required)
master agentx

## default alert threshold to 20% of free space
includeAllDisks 20%

## default alert threshold to 4 on 1 minute, 2 on 5mn and 1 on 15mn
load 4 2 1

## enable link notification on link up/down 
linkUpDownNotifications yes

## enable monitoring (DISMAN), change default FREQUENCY to 10 sec
defaultMonitors yes
monitor -r 10s -o prNames -o prErrMessage "process table" prErrorFlag != 0
monitor -r 10s -o memErrorName -o memSwapErrorMsg "memory" memSwapError != 0
monitor -r 10s -o extNames -o extOutput "extTable" extResult != 0
monitor -r 10s -o dskPath -o dskErrorMsg "dskTable" dskErrorFlag != 0
monitor -r 10s -o laNames -o laErrMessage  "laTable" laErrorFlag != 0
monitor -r 10S -o fileName -o fileErrorMsg  "fileTable" fileErrorFlag != 0

## agentSecName <USER> (required)
agentSecName internal
createUser internal SHA $INTERNAL_USER_AUTH_PASSPHRASE AES $INTERNAL_USER_PRIV_PASSPHRASE

## default full SNMPv1 et SNMPv2c read-only access
## rocommunity <RO-COMMUNITY>
# rocommunity public

## default full SNMPv1 et SNMPv2c to trap-server config
## trapcommunity <TRAP-COMMUNITY>
# trapcommunity $TRAP_COMMUNITY
## trap2sink <TRAP-SERVER>
# trap2sink $TRAP_SERVER_ADDRESS

## default full SNMPv3 read-only access
## rouser <USER>
## FIXME: create view ??
rouser monitor # FIXME
createUser monitor SHA $MONITOR_USER_AUTH_PASSPHRASE AES $MONITOR_USER_PRIV_PASSPHRASE

## send trap using SNMPv3
trapsess -v3 -Ci -l AuthPriv -u $TRAP_USER -a SHA -A $TRAP_USER_AUTH_PASSPHRASE -x AES -X $TRAP_USER_PRIV_PASSPHRASE $TRAP_HOST_ADDRESS:162

```

## 3. Déploiement de la configuration

1. Recopier le modèle de configuration ci-dessus (`snmpd-local.template`) sur le serveur dans le répertoire `/tmp`
2. Définir les variables spécifiques de la configuration

``` sh
$ INTERNAL_USER_AUTH_PASSPHRASE=<passphrase>
$ INTERNAL_USER_PRIV_PASSPHRASE=<passphrase>
$ MONITOR_USER=<username>
$ MONITOR_USER_AUTH_PASSPHRASE=<passphrase>
$ MONITOR_USER_PRIV_PASSPHRASE=<passphrase>
$ TRAP_USER=<username>
$ TRAP_USER_AUTH_PASSPHRASE=<passphrase>
$ TRAP_USER_PRIV_PASSPHRASE=<passphrase>
$ TRAP_HOST_ADDRESS=<hostname>
$ eval "cat <<__EOF"$'\n'"$(cat /tmp/snmpd-local.template)"$'\n'"__EOF"' | sudo tee /etc/snmp/snmpd-local.conf
```
3. Redémarrer le service snmpd

``` sh
$ sudo systemctl restart snmpd
```

