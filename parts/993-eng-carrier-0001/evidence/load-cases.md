# Cas de charge — 993-ENG-CARRIER-0001

Document à remplir **avant** toute géométrie de remplacement. Aucune valeur n'est
pré-remplie : une hypothèse de charge inventée produirait un calcul qui rassure
sans rien prouver.

## 0. Masse et encombrement annoncés — piste à sourcer

| Donnée | Valeur | Lecture |
|---|---|---|
| Masse | 1,96 kg (4,3 lb) | vraisemblablement masse d'expédition, donc pièce plus légère |
| Encombrement | 600 × 50 × 50 mm | vraisemblablement le colis, donc **enveloppe maximale** de la pièce |

Ces deux valeurs ont la forme de données logistiques de revendeur, pas d'un
relevé sur pièce : des cotes de 60 × 5 × 5 cm sont des dimensions de carton, et
une masse d'expédition inclut l'emballage. Elles ne sont donc pas des mesures.

Comme **majorant**, elles restent la première information dimensionnelle du
dossier : la pièce tient dans 600 × 50 × 50 mm.

Recoupement de cohérence : 1,96 kg d'acier représentent environ 250 cm³ de
matière, soit 17 % du volume de cette enveloppe. Compatible avec une lame pliée
ou soudée — ce que le surnom allemand de la pièce, *Schwert*, suggère aussi.

## 1. Ce que la pièce reprend

- Masse du groupe motopropulseur supportée par ce berceau : ____ kg
  - source de la valeur : ____
  - méthode : pesée, documentation officielle, ou répartition mesurée
- Position du centre de gravité par rapport aux points de fixation : ____
- Répartition entre ce berceau et les autres points d'ancrage : ____
- Couple de réaction moteur en première : ____ Nm, bras de levier ____ mm

## 2. Facteurs dynamiques retenus

| Cas | Facteur | Justification et source |
|---|---:|---|
| Vertical, route dégradée | | |
| Freinage longitudinal | | |
| Accélération latérale | | |
| Choc / passage de nid-de-poule | | |
| Sollicitation cyclique de fatigue | | |

Un facteur retenu sans source est une hypothèse : le noter comme telle.

## 3. Interfaces et conditions aux limites

### Couples de serrage — piste à sourcer

| Liaison | Couple annoncé | Statut |
|---|---:|---|
| Support moteur vers berceau | 85 Nm | communiqué, source non établie |
| Berceau vers moteur | 45 à 50 Nm | communiqué comme approximatif, source non établie |

Origine à préciser : manuel d'atelier, fil de forum, ou expérience d'atelier. Le
second est annoncé « around », donc explicitement approximatif. Tant que
l'origine n'est pas connue, aucun des deux n'entre dans un calcul.

Ce qu'ils contraignent une fois confirmés :

- **la précontrainte**, donc l'effort de serrage réellement appliqué au berceau,
  et la pression locale sous tête de vis ;
- **la taille de vis**. Aux valeurs de table usuelles à sec, 85 Nm est cohérent
  avec une M12 classe 8.8, et 45 à 50 Nm avec une M10 classe 8.8. C'est une
  déduction, pas un relevé : la classe réelle et le coefficient de frottement
  changent le résultat ;
- **la faisabilité titane**. Un berceau en Ti-6Al-4V devrait encaisser la même
  précontrainte avec un module presque deux fois plus faible, donc plus
  d'enfoncement local, et avec un risque de grippage que `docs/TITANIUM.md`
  impose déjà de traiter.

- Points de fixation à la caisse : nombre, diamètre, classe de vis, couple de serrage
- Supports moteur : type, raideur, précharge
- Conditions imposées dans le modèle EF (encastrement, appuis, contacts)
- Jeux et tolérances d'assemblage

## 4. Environnement

- Température au voisinage de l'échappement et du moteur : ____
- Vibrations : plage de fréquences d'excitation moteur ____
- Corrosion : sel, humidité, contact avec caisse acier
- Durée de vie visée : ____ km ou ____ heures

## 5. Critères d'acceptation

À définir avant de calculer, sinon le critère s'adapte au résultat :

- Contrainte admissible et coefficient de sécurité retenu : ____
- Déplacement maximal admissible aux interfaces : ____
- Première fréquence propre minimale : ____ Hz
- Tenue en fatigue : nombre de cycles et amplitude ____

## 6. Comparaison de procédés

| Procédé | Masse | Coût | Raideur | Fatigue | Risque | Verdict |
|---|---|---|---|---|---|---|
| Pièce d'origine (référence) | 1,96 kg annoncé | ~225-270 € neuf, non vérifié | référence | fissuration constatée sur la famille | connu | référence |
| Renfort rapporté sur pièce d'origine | + quelques centaines de g | 614 € annoncé, ou soudure atelier | augmentée | vise justement ce défaut | voilage au soudage constaté | **la piste utile** |
| Acier soudé / tubulaire | | | | | | |
| Aluminium usiné | | | | | | |
| Ti-6Al-4V LPBF | ~1,51 kg à raideur égale | milliers d'euros | égale par croissance de section | à qualifier entièrement | grippage, couple galvanique, revue obligatoire | **gain 0,45 kg, soit 0,03 % du véhicule** |

### Ce que la masse annoncée décide

À raideur de flexion égale, le titane ferait gagner environ **0,45 kg** sur cette
pièce — soit **0,03 % de la masse du véhicule**. C'est le prix total du concours.

Pour l'obtenir il faudrait : redessiner les sections, établir des cas de charge
complets, faire une revue d'ingénierie formelle, qualifier un procédé LPBF,
contrôler la pièce, gérer le grippage et le couple galvanique dans un
environnement dont la corrosion est documentée.

`docs/TITANIUM.md` tranche déjà ce cas dans sa liste « quand il ne l'est pas ».
**Sur ces chiffres, le titane n'est pas justifié sur cette pièce.**

Le mode de défaillance observé sur la famille n'est d'ailleurs pas la masse :
c'est la **fissuration**. La pièce utile n'est donc pas une pièce plus légère,
c'est une pièce plus endurante — ce que le marché traite déjà par un renfort à
614 €.

Rappel de `docs/TITANIUM.md` : le titane n'est pas pertinent pour « une pièce
dont la flexion doit rester identique à une pièce acier ». Le module du
Ti-6Al-4V est d'environ 114 GPa contre 210 GPa pour un acier : à géométrie
identique, la pièce serait presque deux fois plus souple. Un gain de masse ne
se constate qu'après avoir redessiné les sections pour retrouver la raideur.

## 7. Revue

- Calcul revu par : ____ (nom de rôle, compétence, date)
- Revue de fabricabilité prestataire : ____
- Plan de validation approuvé : oui / non
- Décision : poursuivre / arrêter / redéfinir
