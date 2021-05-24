# Configuration d'un client collecteur SYSLOG RELP avec RSYSLOG sous Linux

## 1. Prérequis

### 1.1. Debian

* `rsyslog-relp`, et ses dépendances
  * `rsyslog`
* PKI déployée
  * Fichier d'authorité de certification: `/etc/ssl/certs/ca.crt`
  * Fichier certificat du serveur: `/etc/ssl/certs/$HOSTNAME.crt`
  * Fichier non chiffré de clé du certificat de serveur: `/etc/ssl/private/$HOSTNAME.key`

### 1.2. Redhat

* `rsyslog-relp`, et ses dépendances
* PKI déployée
  * Fichier d'authorité de certification: `/etc/pki/ca-trust/source/anchors/ca.crt`
  * Fichier certificat du serveur: `/etc/pki/tls/certs/$HOSTNAME.crt`
  * Fichier non chiffré de clé du certificat de serveur: `/etc/pki/tls/private/$HOSTNAME.key`

## 2. Modèle de configuration

```
## Filename: forwarder-relp.template
## License: MIT (2021)
## Description: template for /etc/rsyslog.d/20-forwarder-relp.conf

# load module
module(load="omrelp")

template (name="template-forward-rfc3164" type="list") {
    constant(value="<")
    property(name="pri")
    constant(value=">")
    property(name="timereported" dateformat="rfc3339")
    constant(value=" ")
    property(name="hostname")
    constant(value=" ")
    property(name="syslogtag" position.from="1" position.to="32")
    property(name="msg" spifno1stsp="on")
    property(name="msg")
}

action(
    name="relp-output"
    type="omrelp"
    target="$SYSLOG_HOST"
    port="514"
    timeout="90"
    conn.timeout="10"
    template="template-forward-rfc3164"

    tls="on"
    tls.cacert="/etc/pki/ca-trust/source/anchors/ca.crt"
    tls.authmode="certvalid"
    tls.myprivkey="/etc/pki/tls/private/$HOSTNAME.key"
    tls.mycert="/etc/pki/tls/certs/$HOSTNAME.crt"

    rebindinterval="100000"

    action.resumeretrycount="-1"
    action.resumeinterval="5"
    action.resumeintervalmax="5"
    action.reportsuspension="on"
    action.reportsuspensioncontinuation="on"

    queue.type="LinkedList"
    queue.size="20000"
    queue.timeoutenqueue="5000"
    queue.dequeuebatchsize="8000"
    queue.workerthreads="2"
    queue.workerthreadminimummessages="7000"

    # disk assisted queue
    queue.maxfilesize="25m"
    queue.maxdiskspace="1g"
    queue.saveonshutdown="on"
    queue.filename="out-relp"
)
```

## 3. Déploiement de la configuration

1. Recopier le modèle de configuration ci-dessous (`forwarder-relp.template`) sur le serveur dans le répertoire `/tmp`
2. Définir les variables spécifiques de la configuration

``` sh
$ SYSLOG_HOST=<hostname>
$ eval "cat <<__EOF"$'\n'"$(cat /tmp/forwarder-relp.template)"$'\n'"__EOF"' | sudo tee /etc/rsyslog.d/20-forwarder-relp.conf
```
3. Redémarrer le service rsyslog

``` sh
$ sudo systemctl restart rsyslog
```

