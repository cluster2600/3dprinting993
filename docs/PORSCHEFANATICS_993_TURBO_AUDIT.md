# Audit local Porsche Fanatics - 993 Turbo

Audit du depot local `C:/Users/MaximeGrenu/porschefanatic.com`, realise le
2026-08-30. Le depot local est le projet du site et contient les donnees
structurees utilisees pour les pages publiques OEM.

## Donnees retrouvees

| Groupe public | Fonction | Lignes PET exposees | References distinctes dans le releve local | Resultat pour le jumeau |
| --- | --- | ---: | ---: | --- |
| [`202-16`](https://porschefanatics.com/oem/993/202-16/) | Turbocharger | 71 | 40 | Nomenclature des deux turbocompresseurs, conduites d'huile, couvercles, boitiers et fixations |
| [`107-20`](https://porschefanatics.com/oem/993/107-20/) | Turbocharging | 65 | 38 | Nomenclature des collecteurs, durites, vannes, capteurs et colliers |
| [`107-45`](https://porschefanatics.com/oem/993/107-45/) | Charge air cooler | 49 | 28 | Nomenclature de l'echangeur, conduits, supports, joints, sondes et durites |

Les ecarts entre lignes et references distinctes viennent des revisions,
variantes gauche/droite et de la presence de deux catalogues PET dans le site
local : le releve KAT 17 et le catalogue Porsche Classic 993. Les donnees
machine-transcrites sont conservees par le site dans `data/oem-listed.json`.

## References K16 confirmees par le releve

Le groupe `202-16` reprend les quatre references Porsche deja associees a la
paire K16 dans le catalogue du jumeau :

- `993 123 013 51` et `993 123 013 52` ;
- `993 123 014 51` et `993 123 014 52`.

Le meme groupe documente aussi les interfaces et sous-ensembles a rechercher,
notamment les conduites d'huile `993 107 125 53` / `993 107 126 53`, les lignes
de ventilation, les supports `993 107 005 52` / `993 107 005 53`, les boitiers
de commande et les joints. Les groupes `107-20` et `107-45` complètent le
contexte d'air comprimé et de refroidissement de charge.

## Mesures et masses déjà disponibles dans le projet

Tu as raison : le projet possède déjà des cotes et des masses de pièces. Elles
sont enregistrées dans le registre de références et les fiches de sources,
avec un niveau de confiance explicite. Quelques exemples utiles au jumeau :

| Pièce ou ensemble | Données disponibles | Nature de la donnée |
| --- | --- | --- |
| Berceau moteur Turbo `993 115 021 53` | `600 x 50 x 50 mm`, `1,96 kg` | Déclaration de fiche produit, déjà structurée dans `catalog/reference/993-declared-part-data.json` |
| Bielle PAUTER 993/993 Turbo | longueur `127,00 mm`, axe `23,01 mm`, logement `58,01 mm`, masse `535 g` | Cotes et masse fabricant, pièce fortement chargée |
| Soupape d'admission 993 Turbo | queue `8 mm`, tête `49 mm`, environ `120 g` | Déclaration de produit, à distinguer de l'encombrement commercial `50 x 110 x 50 mm` |
| Soupape d'échappement 993 Turbo | `108,9 x 43,5 x 8 mm` | Déclaration de produit, sans tolérances ni plan |
| Spoiler arrière Bi-Turbo 993 | `145 x 63 x 27 cm`, `6,7 kg` | Enveloppe et masse aftermarket |
| 993 Turbo complète | environ `1 500 kg` | Masse à vide de variante, pas masse d'une pièce |

Ces valeurs sont déjà dans `catalog/sources/` et, pour les masses et
enveloppes retenues, dans `catalog/reference/`. Elles peuvent alimenter des
bornes, des priors et des contrôles de cohérence du jumeau. Elles ne doivent
pas être converties silencieusement en mesures métrologiques : la plupart sont
des déclarations fournisseur ou des relevés communautaires, sans répétitions,
datums et protocole complet.

## Ce que les pages PET turbo n'apportent pas

Cette collecte PET ne produit pas de nouvelle cote de fabrication pour le K16.
Les pages
signalent elles-mêmes que les lignes sont « transcribed, not read » : une
reference, une description constructeur, une position et une page PET ne
constituent ni une mesure, ni une tolerance, ni un plan de definition.

En particulier, aucun poids public fiable du turbocompresseur K16 lui-même,
aucune masse de CHRA et aucune géométrie cotée de roue ou de carter n'ont été
trouvés dans les trois groupes PET. Les masses du berceau, des soupapes, de la
bielle ou du spoiler ne peuvent pas être attribuées au K16.

Il manque toujours, pour une reconstruction du K16 :

- les diametres, entraxes, profils de brides et reperes d'axe mesures sur une
  piece réelle ;
- les surfaces des roues, volutes, diffuseurs, carters et passages d'huile ;
- les jeux radial/axial, tolérances, rugosités et épaisseurs ;
- les matériaux, traitements thermiques, équilibrage et limites de vitesse ;
- les cartes débit/pression/rendement et les conditions limites d'essai.

Les données du site sont donc intégrées comme source de nomenclature et de
repérage des interfaces dans
`catalog/parts/993-turbocharger-k16-pair-0001.json`. La géométrie reste
`estimated`, sans fichier maître ni revendication d'ajustement.

## Prochaine action utile

Le premier objet à mesurer ou scanner sous licence doit être une pièce non
rotative et non structurelle : conduit froid, support d'echangeur ou adaptateur
de raccordement. Les roues, l'arbre, les paliers, le carter chaud et le CHRA
restent exclus de toute fabrication additive avant revue d'ingénierie,
caractérisation matière, équilibrage et validation dédiés.
