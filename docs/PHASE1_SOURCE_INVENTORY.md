# Phase 1 — Inventaire des sources

Ce document suit l’avancement de la Phase 1. Il n’héberge aucun contenu protégé :
il enregistre où une information se trouve, comment elle a été consultée et ce
que son statut juridique autorise.

## Lot 1 — Catalogues officiels, manuels légalement accessibles et mesures

Consulté le 28 août 2026. Chaque URL a été ouverte avant d’être inscrite ; les
échecs d’accès sont conservés au même titre que les succès.

### Catalogues et documents officiels

| Fiche | Contenu | Accès | Réutilisation | Preuve |
|---|---|---|---|---|
| `SRC-PORSCHE-PET-993` | Catalogue Pièces d’Origine Porsche Classic | disponible | interdite | A |
| `SRC-PORSCHE-NEWSROOM-993` | Dossier historique et gamme | disponible | interdite | A |
| `SRC-PORSCHE-NEWSROOM-993-30Y` | Dossier de presse « 30 ans du 993 » | disponible | interdite | A |
| `SRC-PORSCHE-SHOP-TECHLIT` | Littérature technique officielle à l’achat | disponible, catalogue vide | interdite | non noté |
| `SRC-PORSCHE-CLASSICSHOP-USA` | Ancienne boutique Classic (manuels 993) | hors service (DNS) | interdite | non noté |

### Manuels et données techniques accessibles

| Fiche | Contenu | Accès | Réutilisation | Preuve |
|---|---|---|---|---|
| `SRC-9XXTEILE-PET-DIAGRAMS` | Vues éclatées et numéros de pièces | libre | interdite | C |
| `SRC-PCA-993-ALIGNMENT` | Réglages de trains d’origine | libre | interdite | C |
| `SRC-WIKIPEDIA-993` | Encombrement véhicule et variantes | libre | attribution requise | D |
| `SRC-STUTTCARS-993-PARTS` | Diagrammes PET annoncés | payant | inconnue | non noté |
| `SRC-STUTTCARS-993-TORQUE` | Couples de serrage moteur | payant | inconnue | non noté |

### Mesures et données dimensionnelles

| Fiche | Contenu | Accès | Réutilisation | Preuve |
|---|---|---|---|---|
| `SRC-CARGEOMETRY-993-BODY` | Points de mesure caisse et soubassement | achat (20 USD) | interdite | B |
| `SRC-WHEEL-SIZE-993` | Jantes, déports, entraxe | libre | inconnue | C |
| `SRC-CARFOLIO-993` | Masses et cotes par variante | libre | interdite | D |
| `SRC-RENNLIST-993-FORUMS` | Mesures d’atelier communautaires | bloqué aux robots | inconnue | C |
| `SRC-PELICANPARTS-964-993-FORUM` | Mesures d’atelier communautaires | bloqué aux robots | inconnue | C |

## Sources écartées

Écartées sans être inscrites au registre. Le motif est conservé pour éviter de
les réexaminer.

| Source | Motif |
|---|---|
| Scribd, SlideShare, eManualOnline, eManuals, workshopcarmanuals | Rediffusion du manuel d’atelier Porsche sans droit démontrable |
| Pièces jointes de forum contenant des planches cotées d’usine | Même document protégé, republié par un tiers |
| Agrégateurs de PDF sans éditeur identifiable | Provenance invérifiable |

Une source écartée peut rester utile comme indice de l’existence d’un document.
Elle ne devient jamais une référence du catalogue.

## Constats du lot 1

- Aucun plan coté d’usine n’est légalement accessible librement. Les vues
  éclatées renseignent l’assemblage et la nomenclature, pas la géométrie.
- La donnée dimensionnelle exploitable viendra de la mesure directe, complétée
  par un référentiel de caisse acheté (`SRC-CARGEOMETRY-993-BODY`).
- Les numéros de pièces sont accessibles gratuitement, mais leur rediffusion ne
  l’est pas : ils servent d’identifiant de travail, pas de contenu publié.
- Deux forums majeurs refusent l’accès automatisé ; leur consultation reste
  manuelle et chaque valeur reprise doit être remesurée.
- Le corpus communautaire recopie fréquemment la même origine non citée ; la
  règle « deux copies ne font pas deux confirmations » s’applique directement.

## Lot 2 — Modèles 3D et jumeaux numériques

Recherché en anglais et en allemand le 28 août 2026, sur les places de marché
3D, les boutiques de scans, les services de numérisation et la presse
technique.

### Le constat

**Aucun jumeau numérique public du 993 n'existe.** Ce qui existe se range en
trois catégories, et aucune ne donne une cote :

| Catégorie | Exemple | Niveau | Ce que ça vaut |
|---|---|---|---|
| Maillage visuel de synthèse | modèles de jeu, banques 3D, RWB Sketchfab | D | Silhouette, jamais une interface |
| Scan brut sans échelle | `SRC-SKETCHFAB-993-GT2-RAW-SCAN` | E | Forme, pas mesure |
| Scan commercial de composant | `SRC-BREMAR-3D-SCAN-STORE` | D | Aucun composant 993 |

Le seul modèle 993 sous **licence libre vérifiable** rencontré est le scan brut
du GT2, en CC BY 4.0. Il a été obtenu par vidéogrammétrie sur 115 images tirées
d'une vidéo YouTube : ni échelle, ni précision annoncée, et une chaîne de droits
qui n'est pas étanche puisqu'il dérive d'images appartenant à un tiers.

### Ce qui existe, mais hors de portée

Porsche Classic fait déjà exactement ce travail, en interne
(`SRC-PORSCHE-CLASSIC-3D-PRINTING`) : SLM pour l'acier, SLS pour les polymères,
et « un scan 3D du composant suffit comme base pour lancer la production ». Huit
pièces produites, une vingtaine à l'étude, contrôlées par essai de pression,
tomographie et vérification de montage sur véhicule.

C'est à la fois une validation de la démarche et la barre à franchir. Le
constructeur ne publie pas ces données.

### La piste qui aurait passé à l'échelle, et qui est fermée

`SRC-CAR-CLOUDS-POINT-CLOUDS` vend des nuages de points laser de véhicules
entiers à 195 USD. Un scan de voiture complète donnerait l'environnement de
montage de dizaines de pièces d'un coup, là où une mesure de pièce n'en sert
qu'une : c'était la meilleure réponse au problème d'échelle.

Catalogue interrogé en entier le 28 août 2026 — 906 produits, cinq Porsche :

| Modèle | Prix |
|---|---|
| Porsche 911 Cabriolet (996) 2001 | 195 USD |
| Porsche 911 2015 (991) | 195 USD |
| Porsche Cayenne 2019 et 2020 | 195 USD |
| Porsche Macan 2019 | 195 USD |

**Aucun 993, et aucun refroidi par air.** Le plus proche est un 996 : génération
suivante, caisse entièrement différente. Ce n'est pas un substitut.

Le livrable est un nuage de points E57, intérieur inclus. La piste ne se
rouvrirait que par une commande de numérisation dédiée, d'un tout autre ordre de
prix — ou par un autre prestataire, restant à identifier.

## Lot 3 — Masses d'origine, par la recherche en allemand

`SRC-FEDERLEICHTE-ELFER-993-WEIGHTS` fournit ce qu'aucune source anglophone
n'avait donné : les masses des pièces d'origine du 993, face aux versions
allégées, matière par matière, sur trois pages — extérieur, intérieur, technique.

### Ce qui est directement exploitable par ce projet

Petites pièces d'habillage, non critiques, remplaçables à l'identique :

| Pièce | Origine | Allégée | Gain |
|---|---:|---:|---:|
| Baguettes de porte | 550 g | 170 g | 380 g |
| Planche de bord allégée | 2 100 g | 950 g | 1 150 g |
| Dessus de planche de bord | — | 290 g | — |
| Conduits d'air | — | 35 g | — |
| Cache de chauffage | — | 10 g | — |

Ce sont exactement les formes que le sélecteur fait remonter — `cover strip`,
`cover`, `insert` — et exactement le domaine où l'impression polymère est le bon
procédé.

### Ce que les gros chiffres cachent

Les plus grosses économies de ces tables ne sont **pas** des remplacements :

| Ligne | Gain affiché | Ce que c'est réellement |
|---|---:|---|
| Ensemble de ventilation | 11,4 kg | Dépose du chauffage, pas un remplacement |
| Siège course | 12,5 kg | Touche la retenue des occupants |
| Volant allégé | 1,9 kg | Suppression de l'airbag |
| Portes | 26 kg pièce | Perte des barres anti-intrusion et du vitrage |
| Pavillon | 19,5 kg | Panneau soudé structural |
| Roues, rotules | 1,5 à 3,3 kg | Classe présumée critique par `SAFETY.md` |

Une table de masses ne dit pas ce qu'on a le droit de retirer. Classer avant de
chiffrer, jamais l'inverse.

## Lot 4 — Pages rendues en JavaScript

Plusieurs sources ont été classées inexploitables le 28 août alors qu'elles
n'étaient que **rendues côté client** : la page répondait, mais son contenu
n'existait qu'après exécution du JavaScript. Ce n'est pas un refus, c'est un
problème de rendu — et la distinction change tout, parce qu'un refus se respecte
alors qu'un rendu se résout.

Vérification des `robots.txt` le 29 août 2026 :

| Source | Ce que dit son robots.txt | Verdict |
|---|---|---|
| `porsche.com` (catalogue Classic) | `User-agent: *`, n'interdit que `/api/`, `/search/`, `/login/` et des archives. **Aucun agent nommé.** | **Autorisé** |
| `wheel-size.com` | Autorise `/size/`, n'interdit que `/admin/`, `/api/`, `/data/` et les combinaisons de filtres | **Autorisé** |
| `newsroom.porsche.com` | `allow: /` | Autorisé, et déjà lisible |
| `pcss-tsi.porsche.com` | Le `robots.txt` lui-même renvoie 403 | Hôte fermé, hors de portée |
| `rosepassion.com` | `ClaudeBot` et `Claude-Web` en `Disallow: /` | **Refusé**, voir ADR 0003 |

Les deux premières lignes sont la trouvaille : **le catalogue de pièces officiel
Porsche et les données de jantes sont autorisés**, et leur contenu n'a pas été
lu uniquement faute de moteur de rendu.

Un navigateur sans état exécuté côté serveur — Cloudflare Browser Run, avec son
moteur Kitesurf — lève cet obstacle sans en franchir aucun autre. Il ne change en
revanche **rien** aux deux dernières lignes : un hôte qui renvoie 403 reste fermé,
et un site qui refuse les agents nommés continue de les refuser depuis n'importe
quelle infrastructure.

## Reste à faire en Phase 1

- [x] Modèles 3D sous licence vérifiable — recensés, et le constat est net :
      **aucun jumeau numérique public du 993 n'existe**. Voir le lot 2 ci-dessous.
- [ ] Classement par variante, année et disponibilité
- [x] Pièces manquantes ou difficiles à obtenir — premier cas documenté par une
      source : le berceau moteur Turbo `993 115 021 53` n'a aucune alternative de
      rechange, le berceau tubulaire du marché spécialisé étant explicitement non
      Turbo. Les trois candidats polymères de la phase 2 restent, eux, choisis sur
      critères d'ingénierie et non sur une rareté documentée.
- [ ] Évaluation croisée provenance, licence, précision, réutilisation

État : vingt candidats documentés, le seuil de sortie de phase est atteint en
nombre. Deux des derniers ajouts (`SRC-TEILE-COM-993-ENGINE-CARRIER`,
`SRC-RENNLINE-TUBULAR-ENGINE-CARRIER`) refusent l'accès automatisé : ils comptent
comme candidats recensés, pas comme sources exploitées.
