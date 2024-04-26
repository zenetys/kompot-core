# Activation du HTTPS

Par défaut, Kompot est packagé avec une configuration Apache en HTTP.
Il est également préférable d’activer le HTTPS en amont de l’authentification afin de garantir le chiffrement des données d’authentification qui pourrait circuler sur le réseau.

## Installer les module Apache nécessaires
```
# dnf install mod_ssl
```

## Créer un fichier de configuration Apache
(! dans le cas d'un docker il y a quelques spécificités à prendre en compte dans un paragraphe dédié)
```
# vim /etc/httpd/conf.d/65-auth.conf
```

Avec le contenu suivant :
```
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteCond %{REMOTE_ADDR} !=127.0.0.1
RewriteRule (.*) https://%{HTTP_HOST}$1 [R=302,L]
```

## Modifier le fichier de configuration ssl.conf par défaut
```
# vim /etc/httpd/conf.d/ssl.conf
```

Ajouter le code suivant en fin de section VirtualHost :
```
    [...]
    # Inherit global scope rewrite rules
    RewriteOptions InheritBefore
</VirtualHost>
```
## Générer des certificats autosignés :
Par défaut les clés publique et privée doivent être positionnées dans :
```
  SSLCertificateFile => /etc/pki/tls/certs/localhost.crt
  SSLCertificateKeyFile => /etc/pki/tls/private/localhost.key
```

Ces paramètres peuvent être changés dans le fichier : /etc/httpd/conf.d/ssl.conf

La commande suivante permet de créer les fichiers de certificats aux bons emplacements :
```
  # openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/pki/tls/private/localhost.key -out /etc/pki/tls/certs/localhost.crt
```

## Cas particulier avec un Docker Kompot
### Redirection de port Hôte => Docker
Si votre instance Kompot a été déployée dans un docker, il faut alors prévoir de rediriger le port 8084 de la machine Hôte, vers le port 443 du Docker (comme cela est fait pour le port 8083 => 80)
```
  --publish 0.0.0.0:8084:443/tcp
```
### Ajustement de la configuration apache
Il faut intégrer dans la redirection HTTP vers HTTPS le port 8084. Il faudra donc ajuster la ligne RewriteRule
```
# vim /etc/httpd/conf.d/65-auth.conf
```

Avec le contenu suivant :
```
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteCond %{REMOTE_ADDR} !=127.0.0.1
RewriteRule ^(.*)$ https://%{SERVER_NAME}:8084$1 [R=302,L]
```

# Activation de l’authentification locale
## Ajustement de la configuration apache
```
# vim /etc/httpd/conf.d/65-auth.conf
```

Ajouter le contenu suivant :
```
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

## Créer un compte local
Créer un fichier nouveau fichier .htpasswd correspondant à ce qui a été défini dans la configuration précédente
```
touch /etc/httpd/auth.htpasswd
# chmod 400 /etc/httpd/auth.htpasswd
# chown apache:root /etc/httpd/auth.htpasswd
```

Créer un nouvel utilisateur :
```
# htpasswd -5 /etc/httpd/auth.htpasswd <USER>
  New password: 
  Re-type new password:
```

Supprimer un utilisateur :
```
# htpasswd -D /etc/httpd/auth.htpasswd <USER>
```

# Activation de l’authentification Local + LDAP

Si l'utilisateur existe dans la base locale, il ne sera pas tenté en ldap si l'authentification échoue (password mismatch).
Nécessite un apache 2.4 récent, testé sur el9.

## Installer les module Apache nécessaires
```
# dnf install mod_ldap
```

## Ajustement de la configuration apache
```
# vim /etc/httpd/conf.d/65-auth.conf
```

Ajouter le contenu suivant :
```
LDAPTimeout 5
LDAPRetries 1
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

## Ajouter le certificat du serveur LDAP
```
# cat > /etc/pki/ca-trust/source/anchors/ACME-CERT-CA.crt  # paste in PEM format
# update-ca-trust
```