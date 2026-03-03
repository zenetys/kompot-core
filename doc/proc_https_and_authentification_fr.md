# Activation du HTTPS

Par défaut, Kompot est packagé avec une configuration Apache en HTTP.

Il est préférable d’activer le HTTPS en amont de l’authentification afin de garantir un chiffrement des données d’authentification sur le réseau.

> [!NOTE]
> Dans le cas d'un Kompot en Docker il y a quelques spécificités à prendre en compte : consulter les paragraphes dédiés "Déploiement Kompot par Docker".


## Déploiement Kompot par RPM

#### Installer les module Apache nécessaires

```
# dnf install mod_ssl
```

#### Créer un fichier de configuration Apache

```
# vi /etc/httpd/conf.d/65-auth.conf
```
Coller le contenu suivant :

```apacheconf
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteCond %{REMOTE_ADDR} !=127.0.0.1
RewriteRule (.*) https://%{HTTP_HOST}$1 [R=302,L]
```

#### Modifier le fichier de configuration ssl.conf par défaut

```
# vi /etc/httpd/conf.d/ssl.conf
```

Ajouter le code suivant en fin de section VirtualHost :

```apacheconf
    [...]
    # Inherit global scope rewrite rules
    RewriteOptions InheritBefore
</VirtualHost>
```

#### Générer des certificats autosignés :

Par défaut certificat et clé doivent être positionnées dans :

```apacheconf
SSLCertificateFile /etc/pki/tls/certs/localhost.crt
SSLCertificateKeyFile /etc/pki/tls/private/localhost.key
```

Ces paramètres peuvent être changés dans le fichier `/etc/httpd/conf.d/ssl.conf`.

La commande suivante permet de générer clé et certificat autosigné aux bons emplacements :

```
# openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/pki/tls/private/localhost.key \
    -out /etc/pki/tls/certs/localhost.crt
```

#### Redémarrer Apache

```
# systemctl restart httpd
```


## Déploiement Kompot par Docker

Prérequis :

 * `$VOLUME_ETC_KOMPOT` Chemin du volume /etc/kompot sur le système hôte, ex : `~/app/kompot/etc`
 * `$PUBLISH_HTTPD_TLS_PORT` Adresse HTTPS exposée sur le système hôte, ex : `0.0.0.0:8084`

#### Déposer certificat et clé

Déposer le certificat X509 et sa clé au format PEM dans `$VOLUME_ETC_KOMPOT/certs` :

```
host$ sudo mkdir -p "$VOLUME_ETC_KOMPOT/certs"
host$ sudo tee "$VOLUME_ETC_KOMPOT/certs/kompot.crt" >/dev/null   # coller le certificat
host$ sudo tee "$VOLUME_ETC_KOMPOT/certs/kompot.key" >/dev/null   # coller la clé
host$ sudo chmod 0600 "$VOLUME_ETC_KOMPOT/certs/kompot.key"
```

#### Modifications nécessaires au démarrage du container

Créer ou ajuster le fichier `entrypoint.local` exécuté au démarrage du container :

```
host$ sudo mkdir -p "$VOLUME_ETC_KOMPOT/docker"
host$ cat <<'EOF' |sudo tee "$VOLUME_ETC_KOMPOT/docker/entrypoint.local" >/dev/null
mv /var/cache/dnf /var/lib/kompot/cache-dnf
ln -s /var/lib/kompot/cache-dnf /var/cache/dnf
dnf -y --setopt install_weak_deps=0 --setopt keepcache=1 \
    install mod_ssl mod_ldap
sed -i -r -e 's,^(SSLCertificateFile).*,\1 /etc/kompot/certs/kompot.crt,' \
    -e 's,^(SSLCertificateKeyFile).*,\1 /etc/kompot/certs/kompot.key,' \
    -e '/<\/VirtualHost>/iRewriteOptions InheritBefore' \
    /etc/httpd/conf.d/ssl.conf
EOF
```

Alternatives hors procédure :

* Si le container n'a pas d'accès internet, les RPM à installer (et leurs dépendances) peuvent être téléchargés, déposés dans `$VOLUME_ETC_KOMPOT/rpms` et installés au démarrage du container avec `rpm -Uvh /etc/kompot/rpms/*.rpm`. Cette méthode est préférable pour éviter des problèmes d'accès aux répositories YUM.
* Démarrer un container avec `docker run -it --rm zenetys/kompot bash`, modifier l'image, savegarder avec `docker commit` et utiliser la nouvelle image à la place de `zenetys/kompot`.

#### Redirection automatique des clients en HTTPS

```
host$ sudo vi "$VOLUME_ETC_KOMPOT/httpd/conf.d/65-auth.conf"
```

Ajouter le contenu suivant en reprenant le port définit dans `$PUBLISH_HTTPD_TLS_PORT`, ici 8084 :

```
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteCond %{REMOTE_ADDR} !=127.0.0.1
RewriteCond expr "('%{HTTP_HOST}' =~ m#^([^:]+)#)"
RewriteRule (.*) https://%1:8084$1 [R=302,L]
```

#### Exposer le port HTTPS du container

Rédémarrer le container en exposant un port supplémentaire sur le système hôte avec `--publish "$PUBLISH_HTTPD_TLS_PORT:443/tcp"`.




# Activation de l’authentification locale

## Déploiement Kompot par RPM

#### Ajustement de la configuration apache

```
# vi /etc/httpd/conf.d/65-auth.conf
```

Ajouter le contenu suivant :

```apacheconf
<Location />
    AuthType basic
    AuthName "Authentification required" 
    AuthBasicProvider file
    AuthUserFile /etc/httpd/auth.htpasswd

    Require valid-user
    RequestHeader set X-Remote-User expr=%{REMOTE_USER}
</Location>

<Location /kompot/grafana>
    RequestHeader unset Authorization
</Location>
```

#### Créer un compte local

Créer un fichier nouveau fichier htpasswd à l'emplacement défini précédement :

```
# touch /etc/httpd/auth.htpasswd
# chmod 400 /etc/httpd/auth.htpasswd
# chown apache:root /etc/httpd/auth.htpasswd
```

Pour ajouter un nouvel utilisateur :

```
# htpasswd -5 /etc/httpd/auth.htpasswd <USER>
New password:
Re-type new password:
```

Pour supprimer un utilisateur :

```
# htpasswd -D /etc/httpd/auth.htpasswd <USER>
```

#### Redémarrer Apache

```
# systemctl restart httpd
```


## Déploiement Kompot par Docker

Ce qui suit est effectué depuis le container :

* Obtenir un shell dans le container avec `docker exec -it <CONTAINER_NAME> bash`.
* Effectuer les mêmes opérations que pour un déploiement Kompot par RPM (voir ci-dessus) en remplaçant `/etc/httpd` par `/etc/kompot/httpd` dans les chemins.
* Redémarrer apache avec la commande `zservice restart httpd`.




# Activation de l’authentification locale + LDAP

## Déploiement Kompot par RPM

Si l'utilisateur existe dans la base locale, il ne sera pas tenté en ldap si l'authentification échoue (password mismatch).

> [!NOTE]
> Nécessite un apache 2.4 récent, testé sur el9.

#### Installer le module LDAP pour Apache

```
# dnf install mod_ldap
```

#### Authentification du serveur LDAP

Il s'agit de faire confiance au certificat présenté par le serveur LDAP.

La première option consiste à configurer le système de manière globale. On ajoute ici le certificat de la CA ayant délivré le certificat serveur dans le magasin des autorités de confiance :

```
# cat > /etc/pki/ca-trust/source/anchors/ACME-CERT-CA.crt  # paste in PEM format
# update-ca-trust
```

En alternative il est possible d'utiliser la directive Apache `LDAPTrustedGlobalCert`. On lui spécifie le chemin du certificat de la CA ayant délivré le certificat serveur :

```
# mkdir -p -m 0700 /etc/kompot/certs
# cat > /etc/kompot/certs/ACME-CERT-CA.crt  # paste in PEM format
```

#### Ajustement de la configuration apache

```
# vi /etc/httpd/conf.d/65-auth.conf
```

Ajouter le contenu suivant :

> [!NOTE]
> Si le certificat du serveur LDAP a été déclaré de manière globale au niveau système (méthode `update-ca-trust`), commenter ou supprimer la directive `LDAPTrustedGlobalCert`.

```apacheconf
LDAPTimeout 5
LDAPRetries 1
LDAPTrustedGlobalCert CA_BASE64 /etc/kompot/certs/ACME-CERT-CA.crt
LDAPVerifyServerCert on

<Location />
    AuthType basic
    AuthName "Authentification required" 
    AuthBasicProvider file ldap

    AuthUserFile /etc/httpd/auth.htpasswd

    LDAPReferrals off
    AuthLDAPBindAuthoritative on
    AuthLDAPURL "ldaps://dc01.acme.com:636 dc02.acme.com:636/DC=acme,DC=com?sAMAccountName?sub?(objectClass=user)"
    AuthLDAPInitialBindAsUser on
    AuthLDAPInitialBindPattern (.+) $1@acme.com
    AuthLDAPSearchAsUser on
    AuthLDAPCompareAsUser on
    AuthLDAPRemoteUserAttribute sAMAccountName

    <RequireAny>
        <RequireAll>
            # file
            Require expr "env('AUTHENTICATE_sAMAccountName') == ''" 
            Require valid-user
        </RequireAll>
        <RequireAll>
            # ldap
            Require ldap-filter |\
                (memberOf:1.2.840.113556.1.4.1941:=CN=Domain Admins,CN=Users,DC=acme,DC=com)\
                (memberOf:1.2.840.113556.1.4.1941:=CN=ACME - AdmKompot,OU=ACME-SecurityGroups,DC=acme,DC=com)
        </RequireAll>
    </RequireAny>

    RequestHeader set X-Remote-User expr=%{REMOTE_USER}@ldap env=AUTHENTICATE_sAMAccountName
    RequestHeader set X-Remote-User expr=%{REMOTE_USER}@local env=!AUTHENTICATE_sAMAccountName
</Location>
```

## Déploiement Kompot par Docker

Ce qui suit est effectué depuis le container :

* Obtenir un shell dans le container avec `docker exec -it <CONTAINER_NAME> bash`.
* Pour que `mod_ldap` soit disponible après un redémarrage du container, appliquer la même méthode que pour l'installation de `mod_ssl` (hook via `entrypoint.local` ou image Docker modifiée).
* Effectuer les mêmes opérations que pour un déploiement Kompot par RPM (voir ci-dessus) en remplaçant `/etc/httpd` par `/etc/kompot/httpd` dans les chemins.
* Utiliser la méthode `LDAPTrustedGlobalCert` pour que la configuration soit persistante après redémarrage du container.
* Redémarrer apache avec la commande `zservice restart httpd`.
