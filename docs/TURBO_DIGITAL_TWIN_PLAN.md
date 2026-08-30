# Plan de donnees pour le jumeau numerique du 993 Turbo

Ce document fixe le perimetre avant tout calcul sur Vast.ai. Il ne declare pas
qu'une piece est exacte, ajustee, testee, sure ou liberable.

## Etat de la collecte

| Donnee | Etat | Niveau d'usage |
|---|---|---|
| Architecture biturbo parallele | Confirmee par Porsche | Conditions de contexte |
| Cylindree moteur | 3 600 cm3 | Conditions de contexte |
| Suralimentation maximale de la 993 Turbo de base | 0,8 bar | Cas de charge public, pas limite de conception |
| Puissance/couple de la version de base | 408 ch / 540 Nm | Cas moteur public, pas carte turbo |
| Famille K16 et references 5316-988-6735/6 | Recoupee fabricant/distributeurs | Identification a confirmer |
| References des sous-ensembles K16 | Catalogue fournisseur | Pistes de nomenclature uniquement |
| A/R 8.00 | Declaration TurboMaster sur 5316-988-6735 | A ne pas transformer en cote de fabrication |
| Geometrie 3D et tolerances | Absente | Bloquante |
| Cartes debit/pression/rendement | Absentes | Bloquante pour CFD calibree |
| Materiaux et traitements | Absents par sous-ensemble | Bloquante pour FEA thermique/fatigue |
| Jeux, vitesse rotor, equilibrage | Absents | Bloquante pour rotordynamique |

Les donnees publiques Porsche confirment que les deux turbocompresseurs
fonctionnent en parallele, alimentent chacun un banc et comportent une wastegate
integree. Elles ne constituent pas un plan de definition. Voir les sources
enregistrees dans `catalog/sources/` et la fiche cible
`catalog/parts/993-turbocharger-k16-pair-0001.json`.

## Ce qu'il faut encore obtenir

### Identite et geometrie

- photo lisible de chaque plaque signaletique et identification gauche/droite ;
- numero moteur, annee-modele et configuration exacte : Turbo, Turbo S, GT2 ou
  preparation ;
- scan metrologique ou CAO dont la licence autorise l'usage ;
- repere commun : axe rotor, plans de brides, interfaces huile/air/echappement ;
- surfaces des roues, carters, volute, diffuseur, wastegate et passages d'huile ;
- jeux radial/axial, epaisseurs de paroi, rayons, rugosite et tolerances.

Une photographie, un eclate PET ou une fiche de vendeur ne permet pas de deduire
ces surfaces. Sans piece ou fichier sous licence, la CAO restera un volume
parametrique de recherche, jamais une reproduction.

### Physique et fonctionnement

- points de fonctionnement moteur : regime, debit d'air, pression et temperature
  en entree/sortie ;
- pression et temperature des gaz d'echappement, contre-pression et ouverture de
  wastegate ;
- pression/temperature/debit d'huile et mode de refroidissement du palier ;
- vitesse maximale du rotor et limites surge/choke ;
- historique de fatigue, cycles thermiques et etat d'usure d'un exemplaire.

## Paquet de calcul Vast.ai

Le conteneur `physicsml` est deja prepare pour CAO, maillage, CalculiX,
OpenFOAM, JAX-FEM, PhysicsNeMo et DeepXDE. Le premier job doit rester petit et
reproductible :

1. valider une geometrie parametrique cote froid ;
2. generer un maillage avec rapport de qualite ;
3. executer un cas OpenFOAM de debit/pression ;
4. executer un cas thermique et structural sur la coque avec CalculiX ou
   JAX-FEM ;
5. comparer les sorties a des donnees de reference et conserver les incertitudes ;
6. seulement ensuite entrainer un surrogate Physics ML sur des cas generes par
   solveur.

Le modele de langage peut orchestrer les variantes, verifier les fichiers et
produire des hypotheses. Il ne remplace ni le solveur, ni la metrologie, ni la
qualification du procede additif.

## Premier demonstrateur recommande

Le premier demonstrateur est un adaptateur ou conduit cote froid, non rotatif,
non structurel et accessible a une verification d'encombrement. Le flux de
validation est :

1. parametrage CAO avec plages et incertitudes ;
2. prototype polymerique de montage ;
3. calcul de perte de charge et de temperature ;
4. version metal uniquement apres choix du materiau et du procede ;
5. controle metrologique, pression et temperature dans un banc adapte.

Les roues compresseur/turbine, l'arbre, les paliers, l'actionneur et le carter
chaud restent hors fabrication tant qu'une revue d'ingenierie et un plan de
validation approuve ne sont pas disponibles.

## Critere de lancement

On peut louer Vast.ai lorsque le paquet contient au minimum :

- une geometrie ou un parametrage dont la provenance est explicite ;
- un fichier de conditions aux limites et ses unites ;
- un maillage deterministe et un cas de reference qui tourne localement ;
- une matrice des inconnues et une regle d'arret en cas de depassement ;
- un manifeste des sources, licences, versions du conteneur et hash des entrees ;
- un dossier de sortie separe du depot, avec reprise sur checkpoint.

Ce seuil est atteint pour une etude numerique d'adaptateur cote froid. Il ne
l'est pas pour un jumeau valide du turbocompresseur complet.
