# La supervision doit être accessible

## **"Nagios is all you need"**

Dans la plupart des cas, Nagios™ se suffit à lui-même : c'est un composant simple et fiable qui intègre toutes les fonctions nécessaires aux tâches de supervision.

Néanmoins, il peut paraître complexe aussi nous apportons un mode d'intégration qui permet d'aller à l'essentiel et d'apporter une structure de configuration plus simple et plus claire :

* Les fichiers de configuration ne définissent que les éléments utiles.
* Nagios fonctionne par section et permet de charger des arborescences de fichiers en implémentant lui-même un système de résolution des dépendances de définition, nous adoptons donc un fichier pour un "define" ou section.
* Nous utilisons des variables utilisateurs pour définir de manière "atomique" toutes les variables qui différencient ou peuvent différencier des configurations.

Les infrastructures de la plupart des entreprises sont de tailles raisonnables et peuvent être supervisées par une configuration simple de Nagios sur une machine de dimension raisonnable.

Nous proposons une configuration globale adaptée aux besoins que nous pensons être les plus fréquents, nous proposons une série de modèles d'équipements permettant la supervision sans agent en utilisant le protocole SNMP.

L'utilisateur qui déploie sa configuration va pouvoir avec une série de commande afficher, ajouter ou supprimer des équipements de son périmètre de supervision sans se soucier des attributs spécifiques mais en ayant toujours la possibilité d'aller plus loin dans la définition de ses objets.

## **Métrologie avec RRDTOOL**

RRDTOOL est la deuxième brique essentielle de la supervision. Encore une fois, cette brique est adaptée à des infrastructures de dimension raisonnable. Au-delà, le format de stockage n'est pas adapté à des environnements étendus.

Il est essentiel de ne pas réaliser une double supervision (une pour la disponibilité et une pour la métrologie), d'où l'intérêt de traiter l'ensemble des données collectées par Nagios (elles sont verbeuses) plutôt que de les ignorer. Nagios collecte avec une fréquence habituelle de 5 minutes. Celle-ci peut être diminuée ou augmentée par indicateur ou équipement.

Le projet open-source le plus avancé pour traiter les données collectées par Nagios est PNP4NAGIOS. Ce projet apporte le service "npcd" qui va traiter à intervalles réguliers les données de performances produites par Nagios (host*perfdata / service*perfdata).

L'activation de ce service avec la configuration adaptée permet à lui-seul de générer tous les graphiques permettant de revenir sur un historique de plusieurs semaines sur les données de performance avec une perte de précision adaptée à la période observée et sans engendrer de stockage important.

La représentation des données de métrologie est intégrée dans PNP4NAGIOS. Le serveur Web intégré (Apache) exécute les CGI correspondant aux données souhaitées et les graphiques sont produits par le produit.

## **Vue instantanée : Bac à états**

Nagios est un outil qui collecte à intervalles réguliers des métriques qui donnent lieu à un indicateur de disponibilité. En supervision, il est essentiel de pouvoir être certain que les données représentées dans son tableau de bord de supervision correspondent bien à un instantannée actuel d'état de l'ensemble des indicateurs.

C'est cette supervision active efficace qui a fait de Nagios une référence en matière de supervision.

Nous appelons cette vue instantanée un "bac à états". Il représente au minimum les informations suivantes :

* l'état des équipements
* l'état des services
* un indicateur de rafraîchissement de la vue
* pour chaque indicateur la date ou la durée depuis la dernière mise à jour
* optionnellement : le message détaillé (plugin_output) offrant un premier niveau de diagnostic

Nagios supporte nativement plusieurs états et actions liés à ces états:

* Notification (**NOTIFY**) : l'indicateur doit ou non générer des notifications de changement d'état
* Acquittement (**ACK**) : l'anomalie est prise en compte, il n'est pas nécessaire de poursuivre les notifications jusqu'au prochain changement d'état
* Arrêt programmé (**DOWNTIME**) : une intervention est en cours sur l'équipement ou sur l'indicateur, il n'est pas nécessaire de poursuivre les notifications jusqu'à la fin de la période de l'arrêt programmé
* Tester (**CHECK**) : il est possible de désactiver les tests sur un indicateur jusqu'à nouvel ordre.

Pour plus de détails : <https://www.nagios.org/developerinfo/externalcommands/>

Le bac à état permet de réaliser ces actions en utilisant les fonctions de sécurité intégrées à Nagios.

## **Représentation schématique**

La représentation symbolique est essentielle pour la supervision d'infrastructure. Elle permet d'avoir une vue macroscopique sur son état. L'offre de Nagios est assez faible sur le sujet.

Le projet Open-Source "diagrams.net" regroupe une librairie et une application ouverte, intégrée au navigateur, écrite entièrement en HTML5/JAVASCRIPT/CSS/SVG.

Nous fournissons en open-source les connecteurs qui permettent d'interroger Nagios directement depuis cette interface Web.