# Feuille de route

## Phase 0 — Fondation

Statut : **terminée le 28 août 2026** (`v0.1.0`).

Objectif : rendre le projet contributif avant d’ajouter une pièce.

- [x] Charte et limites de sécurité
- [x] Chaîne d’outils gratuite et ouverte
- [x] Schéma de fiche pièce
- [x] Modèles de mesure et de fabrication titane
- [x] Validation automatique du catalogue
- [x] Templates GitHub de contribution

Critère de sortie : `make check` réussit sur un dépôt propre.

## Phase 1 — Inventaire des sources

Journal détaillé : [docs/PHASE1_SOURCE_INVENTORY.md](docs/PHASE1_SOURCE_INVENTORY.md).

- [x] Recenser catalogues officiels, manuels légalement accessibles et mesures
- [x] Recenser les modèles 3D avec licence vérifiable
- [ ] Classer les références par variante, année et disponibilité
- [ ] Identifier les pièces manquantes ou difficiles à obtenir
- [ ] Évaluer chaque source : provenance, licence, précision, réutilisation

Critère de sortie : vingt candidats documentés, sans importer de contenu non
autorisé. Avancement : dix-huit fiches valides dans `catalog/sources/`.

## Phase 2 — Pilotes polymères

Trois pièces non critiques sélectionnées, fiches créées au statut `concept` :

| Catégorie | Pièce | Fiche |
|---|---|---|
| Géométrique simple, pied à coulisse | Cache d'emplacement d'interrupteur | `993-INT-SWITCH-BLANK-0001` |
| Organique, photogrammétrie | Poignée de tirage de porte | `993-INT-DOOR-PULL-0001` |
| Symétrique ou absente | Cache de glissière de siège | `993-INT-SEAT-RAIL-COVER-0001` |

- [x] Sélectionner trois pièces non critiques
- [x] Écrire un plan de mesure par pièce
- [x] Écrire la géométrie maîtresse pilotée par les mesures (pièce 1)
- [ ] Mesurer les trois pièces sur véhicule
- [ ] Imprimer et monter les prototypes
- [ ] Photographier et consigner les écarts

Critère de sortie : trois prototypes montés, photographiés et mesurés.
**Conditionné à un contributeur disposant des pièces** : voir la contrainte
d'exploitation dans [docs/PROJECT_CHARTER.md](docs/PROJECT_CHARTER.md).

### Piste carrosserie ouverte en parallèle

`993-BODY-FRONT-LID-0001`, capot avant en composite. Retenu comme premier pilote
de carrosserie parce qu'il cumule quatre avantages : panneau **boulonné**, sans
fonction structurale ni barre anti-intrusion ; **surface unique à courbure
douce**, donc le moule le plus simple de la voiture ; **panneau d'origine en
acier**, donc gain réel, avec une référence à battre déjà établie par Porsche
Motorsport à 8 kg en aluminium ; et un **panneau donneur d'occasion peu coûteux**
pour prendre l'empreinte, contrairement aux pièces mécaniques rares.

Masses d'origine établies par une table comparative allemande
(`SRC-FEDERLEICHTE-ELFER-993-WEIGHTS`), ce qui permet enfin de chiffrer le
programme au lieu de l'estimer :

| Pièce | Origine | Carbone | Gain |
|---|---:|---:|---:|
| Capot avant | 14,0 kg | 4,1 kg | **9,9 kg** |
| Ailes avant, la paire | 14,4 kg | 4,4 kg | 10,0 kg |
| Becquet arrière | 12,5 kg | 4,8 kg | 7,7 kg |
| Pare-chocs arrière | 5,05 kg | 3,1 kg | 2,0 kg |
| Rétroviseurs, la paire | 1,8 kg | 0,25 kg | 1,6 kg |
| Bandeau de feux arrière | 1,26 kg | 0,26 kg | 1,0 kg |
| **Total** | **49,0 kg** | **16,9 kg** | **32,1 kg** |

Trente-deux kilos sans toucher à une seule pièce structurale ni supprimer un seul
élément de sécurité — contre 0,45 kg pour le berceau moteur en titane.

Deux lignes de cette table sont volontairement écartées. Les **portes**, 32,0 kg
contre 5,9 kg, affichent le plus gros gain du tableau, mais la version allégée est
une porte de course : le gain vient de la suppression des barres anti-intrusion,
du lève-vitre et du vitrage, pas de la matière. Le **pavillon**, 22,0 kg contre
2,5 kg, est un panneau soudé structural. Ni l'un ni l'autre n'est un remplacement
équivalent.

Les trois dernières puces demandent l'accès physique au véhicule et aux pièces.
Aucune cote n'est estimée en attendant : `parts/993-int-switch-blank-0001/source/switch_blank.py`
refuse de se construire tant que les sept cotes qu'il exige ne sont pas mesurées.

## Phase 3 — Pilote titane

Candidat à l'étude : **berceau moteur `993-ENG-CARRIER-0001`** (993 115 021 53).
Pièce présumée critique au sens de `SAFETY.md`. Le bénéfice du titane n'est pas
acquis : à géométrie identique, la pièce serait environ deux fois plus souple
qu'en acier. Cas de charge et comparaison de procédés à remplir dans
`parts/993-eng-carrier-0001/evidence/load-cases.md` avant toute géométrie.

- [ ] Choisir une pièce où Ti-6Al-4V apporte un bénéfice réel
- [ ] Comparer LPBF, CNC, tôle et fonderie
- [ ] Définir charges, interfaces, environnement et durée de vie
- [ ] Réaliser FEA et revue de fabricabilité avec un prestataire
- [ ] Prototyper en polymère puis, si utile, en aluminium économique
- [ ] Fabriquer un premier exemplaire Ti-6Al-4V traçable

Critère de sortie : rapport matière, fabrication, contrôle et essai disponible.

## Phase 4 — Catalogue public

- [ ] Publier uniquement les pièces ayant franchi leurs portes qualité
- [ ] Générer les pages de catalogue depuis les fiches JSON
- [ ] Ajouter vues, plans cotés et instructions de fabrication
- [ ] Suivre versions, véhicules testés et retours terrain

## Hors périmètre initial

- Commercialisation de pièces
- Homologation routière
- **Remplacement de la structure autoportante**, notamment par un monocoque
  composite. La caisse porte le numéro de châssis, la protection des occupants et
  l'absorption de choc ; un monocoque se conçoit comme tel et ne se traduit pas
  depuis une caisse en tôle ; sa validation passe par des essais de choc
  physiques.

  Précision nécessaire : un tel monocoque **existe commercialement** pour 964 et
  993 (`SRC-ZESAD-CARBON-MONOCOQUE-964-993`), de 129 990 à 219 990 €. Il n'est
  donc pas exclu du périmètre parce qu'il serait impossible, mais parce que ce
  dépôt ne peut ni le documenter, ni le vérifier, ni le reproduire : la fiche
  produit ne publie ni masse, ni raideur en torsion, ni essai de choc, ni
  homologation. Une structure de sécurité sans donnée structurelle publiée est
  exactement ce que `docs/QUALITY_GATES.md` interdit d'inscrire au catalogue.

  Les panneaux de carrosserie, eux, restent un objectif légitime : voir
  `SRC-GUNTHER-WERKS-CARBON-993`, où le restomod de 993 le plus poussé du marché
  habille l'auto de carbone tout en conservant et renforçant la caisse acier.
- Hébergement de manuels ou scans protégés
- Publication de pièces critiques non qualifiées
- Achat ou exploitation d’une machine LPBF
- Modèle IA de substitution avant l’existence d’un corpus FEA/CFD cohérent
