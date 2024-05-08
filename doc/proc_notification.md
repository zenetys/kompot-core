# Activation des notifications

Il est possible de déclencher des commandes dites de notification lorsqu’un indicateur change d'état. Par ce mécanisme, il est donc possible de prévoir un système de notifications par mail, par SMS, …

Le cas d’usage le plus classique étant de mettre en place des notifications par mail, voyons à travers ce document comment cela pourrait se configurer. Il ne s'agit que d’une proposition d’implémentation, chaque contexte peut présenter des spécificités.

La mise en place des notifications repose sur des mécanismes de base de Nagios à mettre en place dans le dossier `/etc/kompot/nagios/objects`.

Pour chaque exemple, il existe souvent plein d'autres paramètres et qui peuvent être surchargés par rapport aux réglages par défaut.
Toutes ces notions sont relatives à Nagios, en complément se référer aux référentiels de Nagios disponibles sur Internet.

## Commandes de notification

Il existe par défaut deux commandes de notificaiton configurées pour envoyer par mail l'état d'un équipement ou d'un service :

* `notify-host-email`
* `notify-service-email`

Ces commandes de notification Nagios s'appuient sur la commande système `mail`, qui devra donc être configurée pour qu'il soit possible d'envoyer des mails avec une commande de ce format :

```bash
echo "<BODY>" | sudo -u nagios /usr/bin/mail -s "<OBJECT>" <EMAIL>
```

Selon la nature des notifications envisagées, il est possible d'ajouter ses propres commandes de notification.

Par défaut, sur les distributions RHEL-like récente, le client `s-nail` est présent et permet d'envoyer simplement des mails avec un fichier de configuration tel que :

```bash
# cat /var/spool/nagios/.mailrc

set v15-compat=yes              
#set smtp-use-starttls
#set ssl-verify=ignore
#set smtp-auth=login    # none / plain / login / oauthbearer
set mta="smtps://<RELAY_SMTP>:<PORT>"
set user="<USERNAME>"
set password="<PASSWORD>"
set from="<FROM_EMAIL>"
```

Plus généralement pour qu'un utilisateur puisse envoyer des mails il faudra créer un fichier ".mailrc" dans le home de l'utilisateur concerné. Pour l'utilisateur nagios (utilisé pour l'envoi des notifications de supervision) son dossier home dans Kompot est `/var/spool/nagios`, pour root c'est `/root`.

Il est aussi possible d'ajouter cette configuration dans un fichier `/etc/s-nail.rc` pour qu'elle s'applique de manière globale à chaque utilisateur.

> [!WARNING]
> Actuellement, dans le cas d'un serveur Kompot sous Docker, seul le fichier lié à l'utilisateur "nagios" (/var/spool/nagios/.mailrc) sera persistant.


## Contact

Chaque email de destination d'une notification doit être configuré sous la forme d'un contact. Il faut créer un fichier de configuration tel que :

```bash
# cat /etc/kompot/nagios/objects/contact_<NAME>.cfg

define contact {
    use                             generic-contact
    contact_name                    <NAME>
    contactgroups                   [+]<GRP_NAME_1>[,<GRP_NAME_2>,...]
    service_notification_period     24x7                 ; service notifications can be sent anytime
    host_notification_period        24x7                 ; host notifications can be sent anytime
    service_notification_options    w,u,c,r,f,s          ; Warning, Unknown, Critical, Recovery, Flapping, Downtime
    host_notification_options       d,u,r,f,s            ; Down, Unreachable, Recovery, Flapping, Downtime
    service_notification_commands   notify-service-email
    host_notification_commands      notify-host-email
    email                           <EMAIL_ADDRESS>
    pager                           <PHONE_NUMBER>
}
```

> [!NOTE]
> Tous les paramètres peuvent être surchargés, sinon ils seront hérités du template `generic-contact`.

Cet exemple se base sur les commandes notification natives de Kompot : `notify-service-email` et `notify-host-email`.
Il est aussi possible de sélectionner sur quels changements d'état de supervision les notifications seront envoyées au contact en question via les paramètres `service_notification_options` et `host_notification_options`, ou encore les périodes de notification.

## Contact groups

Pour faire des envois groupés, il est utile d'associer un contact à un ou plusieurs groupes de contacts via le paramètre "contactgroups" dans le fichier de configuration du contact. Ensuite les contact groups pourront être associé à des hosts, ou template de host.

Par défaut, un contact hérite du modèle de contact `generic-contact` associé à un contact group `default`.
De même, un host hérite du modèle de host 'generic-host' également associé à un contact group `default`.
De cette manière, chaque nouveau contact pourra hériter par défaut d'un système de notification de tous les équipements grâce à ce groupe `default`.

Lors de la déclaration d'un contact, il est préférable d'ajouter un symbole "+" pour conserver les groupes attribués par héritage. Sans le "+", la valeur définie sera appliquée de manière stricte au contact.

```bash
# cat /etc/kompot/nagios/object/contact_<NAME>.cfg

define contact {
    ...
    contact_name    <NAME>
    contactgroups   [+]<GRP_NAME_1>[,<GRP_NAME_2>]
    ...
}
```

Pour déclarer des nouveaux groupes, il faut ajouter des fichiers de configuration nagios tels que :

```bash
# cat /etc/kompot/nagios/object/contactgroup_<GRP_NAME>.cfg

define contactgroup {
    contactgroup_name    <GRP_NAME>
}
```

ou de cette manière si les groupes ne sont pas affectés directement au niveau des contacts :

```bash
# cat /etc/kompot/nagios/object/contactgroup_<GRP_NAME>.cfg

define contactgroup {
    contactgroup_name       <GRP_NAME>
    members                 <NAME_1>,<NAME_2>,...
    contactgroup_members    <GRP_NAME_1>,<GRP_NAME_2>,...
}
```

## Associer des hosts à des contact groups

Le plus simple est d'associer des contact groups directement lors de la création d'un host :

```bash
host <HOSTNAME>:<TYPE> --address=<IP_ADDRESS/DNS> contact_groups=[+]<GRP_NAME_1>[,<GRP_NAME_2>]
```

Lors de la déclaration de contact groups sur un host, il est préférable d'ajouter un symbole "+" pour conserver les groupes attribués par héritage. Sans le "+", la valeur définie sera appliquée de manière stricte et par exemple l'association faite nativement entre le host et le contact group "defaut" ne sera pas faite.

Il est aussi possible d'associer des contact groups à des templates de hosts, il pourra s'agit d'un template dédié au contact_groups ou de manière plus générale être défini d'un un template de host quelconque au niveau de la configuration Nagios :

```bash
# cat /etc/kompot/nagios/object/host_<HOST_TPL_CONTACT>.cfg

define host {
    name            HOST_TPL_CONTACT
    use             generic-host
    register        0
    contact_groups  <GRP_NAME>
}
```

Dans ce cas, il faudra aussi s'assurer que le contact group `<GRP_NAME>` est bien déclaré dans la configuration nagios (voir le point précédent).

Ensuite, il faudra faire hériter de ce template un équipement lors de sa déclaration :

```bash
host <HOSTNAME>:<TYPE> --address=<IP_ADDRESS/DNS> use=HOST_TPL_CONTACT
```
