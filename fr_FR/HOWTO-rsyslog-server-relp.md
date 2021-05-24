# Configuration d'un serveur SYSLOG RELP avec RSYSLOG sous Linux

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
## Filename: server-relp.template
## License: MIT (2021)
## Description: template for /etc/rsyslog.d/10-server-relp.conf

# load module
module(load="imrelp")

input (
    type="imrelp"
    address="0.0.0.0"
    port="2514"
    name="imrelp"
    keepalive="on"
    keepalive.time="30"
    keepalive.interval="30"
    keepalive.probes="6"

    tls="on"
    tls.cacert="/etc/pki/ca-trust/source/anchors/ca.crt"
    tls.authmode="certvalid"
    tls.myprivkey="/etc/pki/tls/private/$HOSTNAME.key"
    tls.mycert="/etc/pki/tls/certs/$HOSTNAME.crt"
)
```

## 3. Déploiement de la configuration

1. Recopier le modèle de configuration ci-dessous (`forward-relp.template`) sur le serveur dans le répertoire `/tmp`
2. Définir les variables spécifiques de la configuration

``` sh
$ SYSLOG_HOST=<hostname>
$ eval "cat <<__EOF"$'\n'"$(cat /tmp/server-relp.template)"$'\n'"__EOF"' | sudo tee /etc/rsyslog.d/10-server-relp.conf
```
3. Redémarrer le service rsyslog

``` sh
$ sudo systemctl restart rsyslog
```

