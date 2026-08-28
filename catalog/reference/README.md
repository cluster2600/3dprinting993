# Données de référence déclarées

Masses, encombrements et matières relevés **chez des tiers**. Rien ici n'a été
mesuré par ce projet, et le fichier le dit à chaque ligne.

Deux garde-fous automatiques :

- chaque entrée porte le `source_id` de la fiche qui l'atteste, et le validateur
  refuse une entrée dont la source n'existe pas au registre ;
- le champ `caveat` signale les cas où la version allégée n'est **pas** un
  remplacement équivalent mais une suppression de fonction ou de sécurité —
  portes de course sans barre anti-intrusion, volant sans airbag, dépose du
  chauffage, panneau soudé structural.

Une masse sans source est une rumeur. C'est exactement ce que ce dossier existe
pour empêcher.

## Squelette d'assemblage

`993-assembly-skeleton.json` porte l'autre moitié du jumeau : **où se trouve
chaque pièce**. Dix systèmes, 239 illustrations, 12 864 références dénombrées,
dérivés d'un catalogue d'usine tenu hors de ce dépôt.

C'est un **agrégat**, et le validateur le maintient tel : une illustration ne
peut porter que son numéro, son dénombrement et ses libellés. Toute clé
supplémentaire — une référence de pièce, par exemple — fait échouer `make check`.

Compter des pièces est un fait ; recopier les lignes d'un catalogue est une
copie. La règle est donc appliquée par le validateur, pas par la bonne volonté.

Régénérer : `python3 scripts/twin_structure.py --listing <atlas>/oem-listed.json --out catalog/reference/993-assembly-skeleton.json`

## Remplir le jumeau : ce qui marche et ce qui ne marche pas

Recherche menée le 28 août 2026 pour trouver les masses des gros ensembles.

**Ne donne rien.** Les forums, allemands compris, pèsent des pièces d'allègement,
jamais des ensembles. Aucune masse publiée pour la boîte de vitesses, les trains,
la caisse nue, le réservoir vide ou le système de freinage. Ce n'est pas une
lacune de recherche : ces valeurs ne sont pas publiées.

**Donne quelque chose.** Les fiches produit de revendeurs portent une masse par
référence. Un seul revendeur rencontré répond à la récupération automatisée et
structure son catalogue par schémas PET, donc dans le même repère que le
squelette d'assemblage : `SRC-ROSEPASSION-993-PARTS`. La masse n'apparaît que
sur la fiche individuelle, une requête par pièce.

**Conséquence de méthode.** Le jumeau ne se remplira pas par ensembles, il se
remplira **référence par référence**, en ciblant celles qui pèsent. Le squelette
dit où elles sont, le sélecteur dit lesquelles comptent, et une fiche revendeur
donne la masse. C'est lent, mais c'est la seule voie qui ne demande pas de
toucher une voiture.
