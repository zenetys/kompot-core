## **Composants techniques**

### **Nagios™**

#### **Description**

Depuis la fin des années 1990, Nagios est la référence en matière d'outil de supervision actif, flexible, fiable et efficace. Même si cette solution présente des limites en termes de scalabilité, c'est une plateforme parfaitement suffisante jusqu'à 10000 points de mesure (indicateurs).

Avec un système de configuration très complet, cette plateforme offre de manière assez légère toutes les briques de base de la supervision : supervision active, supervision passive, interface Web, notification, escalade, modularité en fonction du temps, …

La puissance de Nagios vient également du concept de plugin créé par Ethan Galstad (<https://nagios-plugins.org/doc/guidelines.html>): par une simple commande unix offrir la possibilité de synthétiser une notion de disponibilité, de performance et d'information.

En plus de 20 années d'utilisation, Nagios a réussi à conserver sa modularité et sa relative simplicité tout en gagnant en fiabilité et robustesse.

Une des complexités dans la gestion de Nagios est la production des fichiers de configuration. Avec un peu de pratique, il est assez facile de produire des outils de compilation de structure normalisée exploitable (XLSX, YAML, JSON, …) afin de produire les fichiers de configuration propre et simples traités par Nagios™.

#### **Rôles et fonctions**

Le rôle principal de Nagios est d'ordonnancer des tests et y parvenir Nagios repose sur un structure de fichiers de configuration en texte.

<https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/config.html>

Cette configuration (Object Definition) permet d'établir l'inventaire du périmètre à superviser selon 2 types d'objets :

* les **hosts**, ou équipements, identifiés par un nom et une adresse IP
* les **services**, ou indicateurs, identifiés également par un nom et surtout par une méthode de contrôle (**check_command**) qui décrit comment obtenir l'état de cet indicateur.

Les méthodes de contrôle sont prédéfinies et utilisent les attributs des "hosts" et des "services" pour s'exécuter.

Chaque exécution retourne un état

* **OK** : le test a été exécuté normalement
* **WARNING** : le test a été exécuté normalement mais certaines valeurs de métriques sont dans un intervalle traduisant un risque de disponibilité (un problème de performance conduisant à terme à un problème de disponibilité)
* **CRITICAL** : le test a été exécuté normalement mais certaines valeurs de métriques sont dans un intervalle traduisant un problème de disponibilité (un problème de performance conduisant à terme à un problème de disponibilité)
* **UNKNOWN** : le test n'a pas pu être exécuté normalement, tout ou partie des métriques sont inconnus
* **UP** : pour les équipements, signifie que l'équipement répond correctement, en terme familier, comme le plus souvent c'est un test ICMP qui est attaché à la machine, on peut considérer que l'équipement "pingue"
* **DOWN** : pour les équipements, signifie que l'équipement ne répond pas, par conséquent, tous les services qui y sont rattachés ne peuvent répondre (et ne seront pas testés).
* **UNREACHABLE** : dès lors qu'une notion de parentalité est mise en oeuvre pour décrire des dépendances matérielles entre les équipements, l'état **UNREACHABLE** est retourné lorsqu'un équipement "parent" en terme hiérarchique est **DOWN**, et par conséquent l'équipement ne peut répondre et ne sera pas testé.

Nagios™, à partir des fichiers d'objets, va créer ordonnancer l'exécution des commandes avec une fréquence relativement faible (1 à 10 minutes) afin d'avoir en permanence une image de l'état des équipements supervisés.

Cette image peut être obtenue à l'aide de l'interface de Nagios ou de composants complémentaires.

#### **Informations techniques**

##### Nagios 4

* **Développeur / Editeur** : Ethan Galstad / Nagios
* **Version** : 4.3.4
* **Licence** : GPL (<https://www.nagios.com/legal/licenses/>)

```
$ nagios4 --version
Nagios Core 4.3.4
Copyright (c) 2009-present Nagios Core Development Team and Community Contributors
Copyright (c) 1999-2009 Ethan Galstad
Last Modified: 2017-08-24
License: GPL
Website: https://www.nagios.org

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
```

* **Site Web** : <https://www.nagios.org/>
* **Configuration** : /etc/nagios4/
* **Logs** : syslog, /var/log/nagios4/
* **Contrôle** : systemd

### **RRDTOOL / PNP4Nagios**

#### **Description**

RRDTool est le système de stockage de métrique embarqué par essence. Il est intégré dans bon nombre d'équipement de petite taille et de faible puissance grâce à son fonctionnement optimal. L'usage est contraignant mais dans la plupart des cas, les paramètres peuvent être fixés et répliqués à volonté.

Le système intégré de représentation permet de générer graphique et métrique dans un délai très rapide sur des périodes très longues grâce un système d'historisation implicite offert grâce à des bases de stockage de taille fixe définie à l'initialisation. Cette solution offre une méthode de stockage robuste et fixe dans la durée avec une période d'historisation offrant plusieurs années sur quelques méga-octets.

Nagios produisant des données de performance dans des fichiers plats historisés sur une faible période, PNP4Nagios est l'outil complémentaire qui permet de transformer les données textes produites par Nagios en données RRDTool, avec un minimum de définition grâce à la normalisation apportée par les guidelines de Nagios.

PNP4Nagios offre également une interface pour parcourir les données de métrologie et les exploiter sous forme graphique ou sous forme de données d'export.

#### **Rôles et fonctions**

Représenter les données sous forme de graph.

#### **Informations techniques**

##### RRDTOOL

* **Développeur / Editeur** : Tobias Oetiker
* **Version** : 1.7.1
* **Licence** : GPLv2 (<https://oss.oetiker.ch/rrdtool/license.en.html>)

```
$ rrdtool --version
RRDtool 1.7.1  Copyright by Tobias Oetiker <tobi@oetiker.ch>
               Compiled May 30 2019 20:28:06

Usage: rrdtool [options] command command_options
Valid commands: create, update, updatev, graph, graphv,  dump, restore,
last, lastupdate, first, info, list, fetch, tune,
resize, xport, flushcached
 
RRDtool is distributed under the Terms of the GNU General
Public License Version 2. (www.gnu.org/copyleft/gpl.html)
 
For more information read the RRD manpages
 
```

* **Site Web** : <https://www.rrdtool.org/>
* **Configuration** : (librairie intégrée à PNP4NAGIOS)
* **Logs** : (librairie intégrée à PNP4NAGIOS)
* **Contrôle** : (librairie intégrée à PNP4NAGIOS)

##### **Produit** : PNP4NAGIOS / NPCD

* **Développeur / Editeur** : Joerg Linge / Community
* **Version** : 0.6.26
* **Licence** : GPLv2 (<https://docs.pnp4nagios.org/fr/pnp-0.6/about#licence>)

```
$ npcd --version
npcd 0.6.26 - $Revision: 637 $
 
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as
published by the Free Software Foundation.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 
```

* **Site Web** :
  * <https://github.com/lingej/pnp4nagios>
  * <https://docs.pnp4nagios.org/>
* **Configuration** : /etc/pnp4nagios/
* **Logs** : syslog
* **Contrôle** : systemd

### **Draw.IO / Diagram.net**

#### **Description**

Diagrams.net, anciennement nommé draw.io, est un outil de création WYSIWYG de diagramme avec des fonctionnalités au moins comparables à celles de Microsoft Visio. Cette solution, Open Source, offre l'avantage de fonctionner dans le navigateur et ne nécessite aucun prérequis.

Ce projet Open Source a été adopté et intégré dans un grand nombre de solutions : Google, Sharepoint, Atlassian, Git, Dropbox, Nextcloud, Grafana, …

Les équipes de développement de Zenetys ont implémenté quelques fonctions manquantes ou incomplètes permettant de s'appuyer sur des API temps réels pour donner vie aux schémas :

* Gauges,
* Compteurs,
* Liens,
* Emoticons,
* …

Ces contributions au projet Open Source permettent entre autres de réaliser des représentations dynamiques des données afin de restituer sur un schéma technique ou fonctionnel les changements d'états ou de performance des indicateurs de supervision.

#### **Rôles et fonctions**

* Chargé par le navigateur
* Représentation schématique
* Plugin additionnel apportant une représentation dynamique basée sur des appels REST et des résultats en JSON

#### **Informations techniques**

##### Draw.IO / Diagrams.net / JGraph

* **Développeur / Editeur** : diagrams.net
* **Version** : 14.6+
* **Licence** : Apache License 2.0 (<https://github.com/jgraph/drawio/blob/master/LICENSE>)
* **Site Web** :
  * <https://www.diagrams.net/>
  * <https://github.com/jgraph/drawio>
* **Configuration** : aucune configuration
* **Logs** : console client
* **Contrôle** : navigateur

### **Nagios-Plugins**

#### **Description**

Les plugins permettent la collecte des données là où elles sont disponibles. Nagios a apporté ce principe majeur et universel : il suffit d'ordonnancer intelligemment la collecte normalisée, systématique et reproductible d'indicateurs pour observer les changements dans le fonctionnement des infrastructures et des applications.

Les plugins, ou connecteurs, fournis par Nagios et Centreon offrent une grande couverture fonctionnelle pour l'acquisition active d'indicateurs et de métriques directement vers les équipements et applications et indirectement en passant par des API pour les services Saas.

#### **Rôles et fonctions**

Obtenir l'état d'indicateurs

## 