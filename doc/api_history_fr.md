# API Historique Nagios

Cette API permet d'interroger l'historique des événements Nagios stockés dans une base SQLite. Elle expose trois endpoints :

- `/history` - Recherche dans l'historique brut (états, notifications, commandes externes, événements système)
- `/history/stats` - Statistiques agrégées par période (pour heatmaps/timelines)
- `/history/availability` - Calcul de disponibilité (SLA)

## Base de données

La base SQLite est alimentée par le script `naglog2sql` qui parse les fichiers `nagios.log`. Schéma :

```sql
-- États des hosts/services (alertes, états initiaux)
CREATE TABLE state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hostname TEXT NOT NULL,
  service TEXT,              -- NULL pour les hosts
  state TEXT NOT NULL,       -- OK, WARNING, CRITICAL, UNKNOWN, UP, DOWN, UNREACHABLE
  state_type TEXT NOT NULL,  -- HARD, SOFT
  attempt INTEGER,           -- NULL pour les états au démarrage (INITIAL/CURRENT STATE)
  output TEXT,
  timestamp TEXT NOT NULL
);

-- Notifications envoyées
CREATE TABLE notification (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contact TEXT NOT NULL,
  hostname TEXT NOT NULL,
  service TEXT,              -- NULL pour les hosts
  state TEXT NOT NULL,
  command TEXT,
  output TEXT,
  timestamp TEXT NOT NULL
);

-- Commandes externes (acknowledges, downtimes, etc.)
CREATE TABLE external (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  command TEXT NOT NULL,
  hostname TEXT,
  service TEXT,
  data TEXT,
  timestamp TEXT NOT NULL
);

-- Événements système (log rotation, warnings)
CREATE TABLE system (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event TEXT NOT NULL,
  data TEXT,
  timestamp TEXT NOT NULL
);

-- Cache de disponibilité (populé par naghistory-cache-availability)
CREATE TABLE availability_cache (
  hostname TEXT NOT NULL,
  service TEXT,
  date TEXT NOT NULL,
  available INTEGER NOT NULL DEFAULT 0,
  unavailable INTEGER NOT NULL DEFAULT 0,
  unknown INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (hostname, service, date)
);
```

---

# Endpoint /history

`GET /history`

Interroge la base SQLite d'historique Nagios. Retourne un tableau JSON trié par `timestamp` descendant.

## Paramètres

| Paramètre | Obligatoire | Description |
|-----------|-------------|-------------|
| `action` | non | Table(s) cible, séparées par des virgules : `state`, `notification`, `external`, `system` (défaut : toutes) |
| `hostname` | non | Filtre exact sur le hostname |
| `service` | non | Filtre exact sur le service |
| `state` | non | Filtre sur l'état, multi-valeurs séparées par des virgules (`OK`, `WARNING`, `CRITICAL`, `UNKNOWN`, `UP`, `DOWN`) |
| `since` | non | Timestamp unix : ne retourne que les entrées postérieures ou égales (inclusif) |
| `before` | non | Timestamp unix : ne retourne que les entrées antérieures (exclusif) |
| `period` | non | Période prédéfinie (remplace `since`/`before`) - voir ci-dessous |
| `query` | non | Recherche libre (LIKE) sur les champs texte de la table |
| `limit` | non | Nombre max de résultats (défaut : 500) |
| `hostonly` | non | Si `1`, ne retourne que les entrées host (service null) |
| `initial` | non | Si `0`, exclut les états initiaux (`attempt IS NULL`) de la table `state` |

Les filtres sont cumulatifs (AND).

### Valeurs du paramètre `period`

| Valeur | Description |
|--------|-------------|
| `last-1h` | Dernière heure (fenêtre glissante) |
| `last-6h` | 6 dernières heures |
| `last-12h` | 12 dernières heures |
| `last-24h` | 24 dernières heures |
| `last-7d` | 7 derniers jours |
| `last-30d` | 30 derniers jours |
| `last-90d` | 90 derniers jours |
| `last-365d` | 365 derniers jours |
| `today` | Depuis minuit aujourd'hui |
| `yesterday` | Hier (minuit à minuit) |
| `this-week` | Depuis lundi de cette semaine |
| `last-week` | Semaine précédente (lundi à dimanche) |
| `this-month` | Depuis le 1er du mois |
| `last-month` | Mois précédent |
| `this-year` | Depuis le 1er janvier |
| `last-year` | Année précédente |

## Actions

### `action=state`

Historique des changements d'état des hosts/services (INSERT, plusieurs lignes par host/service).

```
GET /history?action=state
GET /history?action=state&hostname=SRV-01
GET /history?action=state&state=CRITICAL&limit=10
GET /history?action=state&query=DISK
```

Réponse :
```json
[
  {
    "id": 123,
    "hostname": "SRV-01",
    "service": "DISK",
    "state": "WARNING",
    "state_type": "HARD",
    "attempt": 3,
    "output": "WARNING: Storage '/data' Usage 89%",
    "timestamp": "2026-02-02 15:30:00"
  }
]
```

Les hosts ont `service: null`. Les états possibles pour un host sont `UP`, `DOWN`, `UNREACHABLE`.

Cette table contient l'historique complet des états : `CURRENT HOST/SERVICE STATE` (état au démarrage), `INITIAL HOST/SERVICE STATE` (état initial), `HOST/SERVICE ALERT` (transitions d'état), et `HOST/SERVICE FLAPPING ALERT`.

Le champ `attempt` indique le numéro de tentative de check. La valeur `null` identifie les états enregistrés au démarrage de Nagios (`INITIAL` et `CURRENT STATE`), par opposition aux vraies alertes (`HOST/SERVICE ALERT`).

Le champ `query` cherche dans `hostname`, `service` et `output`.

### `action=notification`

Historique des notifications envoyées (INSERT, plusieurs lignes par host/service).

```
GET /history?action=notification
GET /history?action=notification&hostname=SRV-01&limit=20
```

Réponse :
```json
[
  {
    "id": 42,
    "contact": "admin-email",
    "hostname": "SRV-01",
    "service": "DISK",
    "state": "WARNING",
    "command": "notify-service-email",
    "output": "WARNING: Storage '/data' Usage 89%",
    "timestamp": "2026-02-02 15:30:00"
  }
]
```

Les notifications host ont `service: null`. Le champ `query` cherche dans `hostname`, `service`, `contact` et `output`.

### `action=external`

Historique des commandes externes Nagios (INSERT).

```
GET /history?action=external
GET /history?action=external&hostname=SRV-01
GET /history?action=external&hostname=SRV-01&service=DISK
```

Réponse :
```json
[
  {
    "id": 100,
    "command": "ACKNOWLEDGE_SVC_PROBLEM",
    "hostname": "SRV-01",
    "service": "DISK",
    "data": "2;0;1;admin;acknowledged",
    "timestamp": "2026-02-02 14:00:00"
  }
]
```

Les commandes sont parsées pour extraire `hostname` et `service` selon le type :
- Commandes service (`*_SVC_*`) : `hostname` et `service` extraits
- Commandes host (`*_HOST_*`) : `hostname` extrait, `service` vide
- Autres : `hostname` et `service` vides

Le champ `data` contient les paramètres restants après hostname/service.

Le champ `query` cherche dans `hostname`, `service`, `command` et `data`.

### `action=system`

Événements système Nagios (INSERT) : log rotation, warnings internes, etc.

```
GET /history?action=system
```

Réponse :
```json
[
  {
    "id": 1,
    "event": "LOG ROTATION",
    "data": "DAILY",
    "timestamp": "2026-02-02 00:00:00"
  }
]
```

Le champ `query` cherche dans `event` et `data`. Les paramètres `hostname` et `state` ne s'appliquent pas à cette table.

### Actions multiples

Le paramètre `action` accepte plusieurs valeurs séparées par des virgules. La réponse est un UNION de toutes les tables demandées, triée par `timestamp` descendant, avec le `LIMIT` appliqué globalement.

```
GET /history?action=state,notification&limit=10
GET /history?action=state,notification,external,system&query=SRV-01
```

En mode multi-tables, chaque objet JSON contient un champ `_type` indiquant la table source (`state`, `notification`, `external` ou `system`). Les colonnes absentes d'une table sont retournées à `null`.

Réponse :
```json
[
  {
    "_type": "state",
    "hostname": "SRV-01",
    "service": "DISK",
    "state": "WARNING",
    "state_type": "HARD",
    "attempt": 3,
    "contact": null,
    "command": null,
    "output": "WARNING: Storage '/data' Usage 89%",
    "event": null,
    "data": null,
    "timestamp": "2026-02-02 15:30:00"
  },
  {
    "_type": "notification",
    "hostname": "SRV-01",
    "service": "DISK",
    "state": "WARNING",
    "state_type": null,
    "attempt": null,
    "contact": "admin-email",
    "command": "notify-service-email",
    "output": "WARNING: Storage '/data' Usage 89%",
    "event": null,
    "data": null,
    "timestamp": "2026-02-02 15:30:00"
  }
]
```

Avec une seule action, la réponse reste identique au format original (sans champ `_type`, sans colonnes `null`).

Les filtres `hostname`, `service`, `state` ne s'appliquent qu'aux tables qui possèdent ces colonnes. Les filtres `since` et `query` s'appliquent à toutes les tables.

## Erreurs

En cas d'erreur, le CGI retourne un `Status: 500` avec un header `X-Error`.

| Cas | Message |
|-----|---------|
| `action` inconnu | `unknown action 'xxx'` |
| Base inaccessible | `database not found: /path/to/db` |

---

# Endpoint /history/stats

`GET /history/stats`

Retourne le nombre d'événements agrégés par période de temps, pour afficher une heatmap/timeline sans charger tous les événements bruts.

## Paramètres

| Paramètre     | Obligatoire | Description |
|---------------|-------------|-------------|
| `granularity` | non | Période d'agrégation : `hour`, `day` (défaut), `week`, `month` |
| `days`        | non | Nombre de jours à couvrir (défaut : 365) |
| `before`      | non | Timestamp Unix de fin (défaut : maintenant) |
| `period`      | non | Période prédéfinie (remplace `days`/`before`) : voir `/history` |
| `action`      | non | Filtrer par type(s) : `state`, `notification`, `external`, `system` (défaut : tous) |
| `state`       | non | Filtrer par état(s) : `OK`, `WARNING`, `CRITICAL`, `UNKNOWN` |
| `hostonly`    | non | `1` = hôtes uniquement (service null) |
| `initial`     | non | Si `0`, exclut les états initiaux (`attempt IS NULL`) de la table `state` |
| `query`       | non | Recherche texte (hostname, service) |

## Exemples

```
GET /history/stats
GET /history/stats?granularity=day&days=365
GET /history/stats?granularity=hour&days=7
GET /history/stats?granularity=day&days=365&action=state,notification
GET /history/stats?granularity=day&state=CRITICAL,WARNING
```

## Réponse

```json
{
  "granularity": "day",
  "from": "2025-02-03",
  "to": "2026-02-03",
  "data": [
    { "date": "2026-02-03", "count": 42 },
    { "date": "2026-02-02", "count": 158 },
    { "date": "2026-02-01", "count": 87 },
    { "date": "2026-01-31", "count": 12 }
  ]
}
```

Les dates sont triées par ordre décroissant (`timestamp DESC`). Les périodes sans événements sont omises.

### Formats de date selon la granularité

| Granularité | Format | Exemple |
|-------------|--------|---------|
| `hour` | `YYYY-MM-DD HH:00` | `2026-02-03 14:00` |
| `day` | `YYYY-MM-DD` | `2026-02-03` |
| `week` | `YYYY-WWW` | `2026-W05` |
| `month` | `YYYY-MM` | `2026-02` |

Les dates sont en UTC.

## Erreurs

| Cas | Message |
|-----|---------|
| `granularity` invalide | `invalid granularity 'xxx'` |
| `action` inconnu | `unknown action 'xxx'` |
| Base inaccessible | `database not found: /path/to/db` |

---

# Endpoint /history/availability

`GET /history/availability`

Calcule le taux de disponibilité d'un host ou service sur une période donnée.

## Calcul

### États effectifs

Pour les **hosts** (2 colonnes) :

| État host | → Catégorie |
|-----------|-------------|
| `UP` | available |
| `DOWN` | unavailable |
| `UNREACHABLE` | unknown |
| `DELETED` | unknown |

Pour les **services** (3 colonnes, avec corrélation host) :

| État host | État service | → Catégorie |
|-----------|--------------|-------------|
| `DOWN` | * | **unknown** |
| `UNREACHABLE` | * | **unknown** |
| `UP` | `OK`, `WARNING` | available |
| `UP` | `CRITICAL` | unavailable |
| `UP` | `UNKNOWN` | unknown |
| * | `DELETED` | unknown |

**Note importante** : Quand un host est DOWN, l'état du service est considéré comme **unknown** (on ne peut pas vérifier l'état réel du service).

### Formule

```
disponibilité = available / (available + unavailable) * 100
```

Les périodes en état `unknown` ne sont pas comptabilisées dans le calcul.

### État DELETED

L'état `DELETED` est inséré automatiquement par le script `naghistory-mark-deleted` pour les hosts/services qui n'ont pas reçu de mise à jour depuis un certain temps (par défaut 24h). Cela permet de gérer :
- Les services désactivés
- Les hosts supprimés du monitoring

Cet état est traité comme `unknown` dans le calcul de disponibilité.

## Paramètres

| Paramètre  | Obligatoire | Description |
|------------|-------------|-------------|
| `hostname` | non* | Host à interroger |
| `service`  | non | Service à interroger (si omis : disponibilité host) |
| `since`    | non | Timestamp Unix de début (défaut : il y a 30 jours) |
| `before`   | non | Timestamp Unix de fin (défaut : maintenant) |
| `period`   | non | Période prédéfinie (remplace `since`/`before`) : voir `/history` |
| `all`      | non | Si `1`, retourne toutes les combinaisons host+service (mode bulk) |

*`hostname` est requis sauf si `all=1`.

## Exemples

```
GET /history/availability?hostname=SRV-01
GET /history/availability?hostname=SRV-01&service=DISK
GET /history/availability?hostname=SRV-01&since=1704067200&before=1706745600
GET /history/availability?all=1
```

## Réponse (mode simple)

```json
{
  "hostname": "SRV-01",
  "service": "DISK",
  "from": "2026-01-05T00:00:00Z",
  "to": "2026-02-04T00:00:00Z",
  "availability": 99.8521,
  "durations": {
    "available": 2587200,
    "unavailable": 3840,
    "unknown": 1200,
    "total": 2592000
  }
}
```

## Réponse (mode bulk avec `all=1`)

```json
{
  "from": "2026-01-05T00:00:00Z",
  "to": "2026-02-04T00:00:00Z",
  "total_period": 2592000,
  "cached": true,
  "data": [
    {"hostname": "SRV-01", "service": null, "availability": 100.0, "available": 2592000, "unavailable": 0, "unknown": 0},
    {"hostname": "SRV-01", "service": "DISK", "availability": 99.8521, "available": 2587200, "unavailable": 3840, "unknown": 1200},
    {"hostname": "SRV-02", "service": "CPU", "availability": 98.5, "available": 2553120, "unavailable": 38880, "unknown": 0}
  ]
}
```

Les durées sont en secondes.

Le champ `cached` indique si les résultats proviennent de la table de cache (`true`) ou ont été calculés à la volée (`false`). Les requêtes utilisant le cache sont ~15-20x plus rapides.

## Cache

Le mode bulk utilise automatiquement une table de cache (`availability_cache`) si elle couvre au moins 90% de la période demandée. Cette table stocke les durées agrégées par jour pour chaque combinaison host+service.

Pour maintenir le cache à jour, exécutez le script `naghistory-cache-availability` quotidiennement via cron :

```bash
# Rafraîchir les jours manquants + aujourd'hui (mode incrémental)
/path/to/scripts/naghistory-cache-availability -d /path/to/nagios-history.db

# Forcer le recalcul complet des 365 derniers jours
/path/to/scripts/naghistory-cache-availability -d /path/to/nagios-history.db -f

# Options
#   -d, --db PATH       Chemin de la base (défaut: /var/lib/kompot/nagios/nagios-history.db)
#   -D, --days N        Nombre de jours à cacher (défaut: 365)
#   -f, --force         Forcer le recalcul de tous les jours
#   -v, --verbose       Afficher la progression
```

## Erreurs

| Cas | Message |
|-----|---------|
| `hostname` manquant | `missing hostname parameter` |
| Base inaccessible | `database not found: /path/to/db` |

---

# Scripts de maintenance

## naghistory-cache-availability

Pré-calcule la disponibilité quotidienne et la stocke dans la table `availability_cache`. Doit être exécuté quotidiennement via cron.

```bash
# Usage
naghistory-cache-availability [-d database] [-D days] [-f] [-v]

# Options
#   -d, --db PATH       Chemin de la base (défaut: /var/lib/kompot/nagios/nagios-history.db)
#   -D, --days N        Nombre de jours à cacher (défaut: 365)
#   -f, --force         Forcer le recalcul de tous les jours
#   -v, --verbose       Afficher la progression

# Exemples
naghistory-cache-availability -d /var/lib/kompot/nagios/nagios-history.db -v
naghistory-cache-availability -d /var/lib/kompot/nagios/nagios-history.db -f -D 30
```

Le cache tient compte de la corrélation host+service : quand un host est DOWN, tous ses services sont considérés comme `unknown`.

## naghistory-mark-deleted

Marque les hosts/services inactifs comme `DELETED` dans la table `state`. Doit être exécuté régulièrement (quotidiennement recommandé).

```bash
# Usage
naghistory-mark-deleted [-d database] [-t stale_after] [-n] [-v]

# Options
#   -d database     Chemin de la base (défaut: /var/lib/kompot/nagios/nagios-history.db)
#   -t stale_after  Délai en secondes avant marquage (défaut: 86400 = 24h)
#   -n              Mode dry-run (affiche sans modifier)
#   -v              Mode verbeux

# Exemples
# Voir ce qui serait marqué (dry-run)
naghistory-mark-deleted -d /var/lib/kompot/nagios/nagios-history.db -n -v

# Marquer les hosts/services inactifs depuis 48h
naghistory-mark-deleted -d /var/lib/kompot/nagios/nagios-history.db -t 172800

# Exécution standard
naghistory-mark-deleted -d /var/lib/kompot/nagios/nagios-history.db
```

Ce script détecte les hosts/services qui :
1. N'ont pas reçu de mise à jour depuis `stale_after` secondes
2. N'ont pas déjà un état `DELETED`

Il insère alors un état `DELETED` avec le timestamp actuel.

## availability-calc

Calcule la disponibilité à partir de données d'état. Utilisé en interne par les tests et peut être utilisé en ligne de commande.

```bash
# Usage
availability-calc -v SINCE=<timestamp> -v BEFORE=<timestamp>

# Entrée (stdin, tab-separated)
# Mode 2 colonnes (host) : timestamp<TAB>state
# Mode 3 colonnes (service) : timestamp<TAB>host_state<TAB>service_state

# Sortie (tab-separated)
# available<TAB>unavailable<TAB>unknown<TAB>availability%

# Exemples
# Host simple
echo -e "0\tUP\n500\tDOWN" | availability-calc -v SINCE=0 -v BEFORE=1000
# Résultat: 500     500     0       50.0000

# Service avec corrélation host
echo -e "0\tUP\tOK\n300\tDOWN\tOK\n600\tUP\tOK" | availability-calc -v SINCE=0 -v BEFORE=1000
# Résultat: 700     0       300     100.0000
# (300-600: host DOWN → service unknown)
```

Le script supporte les timestamps Unix et ISO :
```bash
echo -e "2026-01-01 00:00:00\tOK" | availability-calc \
  -v SINCE="2026-01-01 00:00:00" -v BEFORE="2026-01-02 00:00:00"
```

---

# Cron recommandé

```cron
# Mise à jour du cache de disponibilité (après minuit pour avoir la journée complète)
5 0 * * * /opt/kompot/bin/naghistory-cache-availability -d /var/lib/kompot/nagios/nagios-history.db

# Marquage des hosts/services supprimés
10 0 * * * /opt/kompot/bin/naghistory-mark-deleted -d /var/lib/kompot/nagios/nagios-history.db

# Import des logs Nagios (toutes les 5 minutes)
*/5 * * * * /opt/kompot/bin/naglog2sql -d /var/lib/kompot/nagios/nagios-history.db /var/nagios/nagios.log
```
