# 3dprinting993

Projet ouvert de rétroconception et de fabrication de pièces pour la Porsche
911 type 993, avec un accent particulier sur les pièces en titane fabriquées par
fusion laser sur lit de poudre (LPBF/DMLS).

L'objectif est un **jumeau numérique** de la 993. Pas une image de synthèse : un
modèle du véhicule pièce par pièce, où chaque élément porte sa référence, sa
place dans l'assemblage, sa variante, sa masse, sa matière et son encombrement,
chacun relié à une source vérifiable.

Deux jumeaux sont possibles, et ils n'ont pas le même coût :

- le **jumeau géométrique**, où chaque pièce existe en CAO. Il exige la pièce
  physique, donc un contributeur ou une donnée achetée. Il avance pièce par
  pièce ;
- le **jumeau structurel**, où chaque pièce existe comme donnée : référence,
  arborescence, applicabilité, masse, matière, enveloppe. Il se construit à
  partir de catalogues et de sources publiques, sans toucher une voiture.

Ce dépôt construit le second et prépare le premier. L'avancement se mesure, il ne
se raconte pas :

```bash
python3 scripts/twin_coverage.py
```

La couverture massique dit quelle part de la masse à vide est décrite par des
pièces dont la masse est documentée et sourcée. Tout le reste est le travail qui
reste.

## Principes

- **Source avant STL** : FreeCAD, OpenSCAD ou STEP restent les formats maîtres.
- **Preuve avant publication** : chaque affirmation de compatibilité ou de
  précision doit être reliée à une mesure ou une source.
- **Prototype avant métal** : tout montage est validé en polymère avant une
  fabrication titane coûteuse.
- **Sécurité explicite** : une pièce critique reste bloquée tant que son analyse,
  son procédé et ses essais ne sont pas approuvés.
- **Outils accessibles** : la chaîne locale utilise en priorité des logiciels
  gratuits et open source. La préparation machine LPBF et la fabrication finale
  peuvent dépendre du prestataire industriel.

## Démarrage rapide

Prérequis : Python 3.11 ou plus récent et `make`.

```bash
make check
cp templates/part-record.json catalog/parts/993-xxx-0001.json
```

Compléter ensuite la fiche, ajouter les fichiers CAO autorisés dans
`parts/<part_id>/`, puis relancer `make check`.

## Organisation

```text
catalog/parts/       fiches structurées des pièces
catalog/sources/     registre des sources, droits et niveaux de preuve
catalog/manual/      registre quantitatif dérivé du manuel 993, avec pages
catalog/measurements/ séances de mesure, instruments et incertitudes
parts/               géométries et livrables par pièce
schemas/             contrat de données du catalogue
containers/          images de calcul reproductibles, GPU et CPU
templates/           modèles de fiche, mesure et demande de fabrication
docs/                plan, outils, workflows et critères qualité
scripts/             contrôles automatiques sans dépendance externe
tests/               tests du catalogue et de ses garde-fous
```

## État

La **Phase 0 — Fondation** est terminée. La **Phase 1 — Inventaire des
sources** est engagée : catalogues officiels, manuels accessibles et sources de
mesure sont recensés dans `catalog/sources/`
(voir [docs/PHASE1_SOURCE_INVENTORY.md](docs/PHASE1_SOURCE_INVENTORY.md)). La
[cartographie du manuel 993](docs/993_MANUAL_DATA_MAP.md) relie désormais les
données publiques de Porsche Fanatics aux pages techniques du manuel, sans
importer le PDF ni créer de fausses mesures.
Aucune pièce n’est encore déclarée imprimable ou validée. Voir
[ROADMAP.md](ROADMAP.md) et [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md).

## Avertissement

Ce dépôt fournit des données de recherche et de fabrication sans garantie.
L’impression, le montage et l’utilisation sur route restent sous la
responsabilité de la personne qui fabrique et installe la pièce. Lire
[SAFETY.md](SAFETY.md) avant toute fabrication.

Porsche et 911 sont des marques de leurs détenteurs respectifs. Ce projet est
indépendant et non affilié à Porsche AG.

## Licence

Les contributions originales du dépôt sont sous licence MIT sauf indication
contraire dans la fiche d’une pièce. Les sources et modèles tiers conservent
leur propre licence. Voir [LICENSES.md](LICENSES.md).
