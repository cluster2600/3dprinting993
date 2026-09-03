# F40 — référence 935 pour la nouvelle culasse 917 refroidie par air

## Décision de géométrie

La nouvelle culasse conserve par défaut la morphologie extérieure du scan 935 :
corps quasi rectangulaire, ailettes droites, bossages locaux, une interface
d'admission, une interface d'échappement et double allumage. Le noyau elliptique
global F39 est rejeté : il provenait d'un ajustement de boîte englobante et son
écart scan vers B-Rep P95 de 16,02 unités ne démontrait aucun bénéfice.

La variante quatre soupapes sera une modification **interne et locale**. Chaque
conduit extérieur d'origine est conservé puis bifurqué en Y vers deux soupapes.
Une modification extérieure ne peut être retenue qu'après comparaison A/B sur
le même modèle, le même maillage convergé et les mêmes conditions aux limites.

## Variantes 935 à ne pas mélanger

| Famille | Refroidissement | Usage dans F40 |
| --- | --- | --- |
| 935 refroidie par air, culasse `930 104 048 01`, date `10-78` | ailettes et air forcé | référence morphologique et contrôles documentaires |
| 935/78 « Moby Dick » | culasses refroidies par eau, mult soupapes | exclue comme référence de forme et de refroidissement |

Porsche présente officiellement la 935/78 comme sa première voiture de course à
culasses refroidies par eau. Employer ses culasses pour corriger le scan
refroidi par air mélangerait deux architectures thermiques incompatibles.

## Cotes documentaires recoupées

| Paramètre | Valeur | Source | Usage |
| --- | ---: | --- | --- |
| hauteur de culasse 935 | 84,20–84,21 mm | Retro Sport, jeu daté `10-78` | contrôle d'échelle à compléter sur les deux plans correspondants du scan |
| conduit admission 935 | 41 mm | Retro Sport | contrôle du raccord externe unique |
| conduit échappement 935 | 40 mm | Retro Sport | contrôle du raccord externe unique |
| référence | `930 104 048 01` | Retro Sport | identification documentaire de la pièce photographiée |
| soupapes | 12 TRW remplies de sodium pour 6 culasses | Retro Sport | architecture historique 2V ; aucune transposition automatique au concept 4V |
| guide échappement | refroidissement d'huile déclaré | Retro Sport | piste hydraulique à reconstruire et à ouvrir au dépoudrage |
| soupape admission 917 4,494 l | 47,5 mm | fiche FIA n° 250, p. 9 | témoin historique 2V |
| soupape échappement 917 4,494 l | 40,5 mm | fiche FIA n° 250, p. 9 | témoin historique 2V |
| levée admission / échappement 917 | 12,1 / 10,5 mm | fiche FIA n° 250, p. 9 | limites documentaires, pas une loi de came complète |
| conduit admission 917 | 41 mm, tolérance supérieure publiée 0,8 mm | fiche FIA n° 250, p. 10 | témoin de raccord et entrée CFD |

Le rapport d'interface du scan trouve environ 41,40–41,60 unités sur plusieurs
sections du raccord `high_B` et 40,04–40,71 unités sur les sections utilisables
du raccord `low_B`. La cohérence avec 41 et 40 mm soutient la convention de
travail proche de `1 unité OBJ = 1 mm`, mais ce recoupement entre une annonce et
un scan non identifié par chaîne de garde n'est pas une certification
métrologique.

L'audit exécutable F40 ajoute un troisième contrôle indépendant : la hauteur du
scan depuis le plan de deck ajusté est de 84,000 unités, contre 84,20–84,21 mm
pour le jeu de culasses publié. La médiane des contrôles de raccord vaut environ
0,98822 mm/unité alors que le contrôle de hauteur vaut environ 1,00244
mm/unité, soit un écart relatif de 1,44 %. Cet écart est assez faible pour
retenir `1 unité OBJ = 1 mm` comme convention de calcul, mais trop important et
trop mal traçable pour remettre automatiquement le scan à l'échelle. La
géométrie n'est donc pas redimensionnée.

Le catalogue Porsche d'échange confirme les familles de références 930 et les
variantes moteur, mais ne décrit pas directement la pièce de course
`930 104 048 01`. Ses valeurs ne remplacent donc ni celles du scan, ni celles de
la fiche FIA 917. Le couple `32/38 mm` extrait pour certaines culasses Turbo est
ambigu et n'est pas utilisé comme diamètre de soupape.

## Recherche allemande et tri des photographies

La galerie Retro Sport contient 23 vues de la même série de culasses. Elle
permet de contrôler le marquage moulé `930.104.341.2R`, le code `10-78`, les
deux sièges, le double allumage, les ailettes et les deux raccords. Une annonce
allemande NOS d'Automobilia Ladenburg associe indépendamment le même marquage
moulé à une culasse 935. Ces images renforcent l'identification, mais leur
perspective ne ferme aucune cote.

La table LN Engineering associe la culasse Turbo de série moulée
`930.104.341.2R` à des soupapes `49/41,5 mm`, des conduits `32/36 mm` et une
chambre de `90 cm3`. Elle est secondaire et ne décrit pas la préparation de
course `930 104 048 01`, publiée avec des raccords `41/40 mm`. Elle n'est donc
utilisée que comme contrôle de famille : transposer ses soupapes ou ses
conduits à F40 serait une confusion de variante.

La chronologie allemande officielle Porsche confirme la séparation thermique :
les 935 de 1976 et 1977 précèdent la 935/78, pour laquelle Porsche introduit les
culasses mult soupapes refroidies par eau. Le concept F40 reste volontairement
un développement nouveau à quatre soupapes **refroidi par air**, installé dans
l'enveloppe 935 scannée; il ne doit jamais être présenté comme une culasse
historique Moby Dick.

## B-Rep extérieur exécuté

La première porte est maintenant franchie sur la peau latérale extérieure :

- 30 coupes du stock Poisson scan-conforme ont été transformées en profils
  B-spline fermés locaux ;
- les 14 ailettes emploient chacune leur propre coupe, sans rayon elliptique
  commun ;
- le loft OCCT réglé produit un unique solide STEP réimportable ;
- l'écart stock vers peau latérale vaut `0,400` unité en médiane et `1,806` au
  P95 ;
- l'écart des contours bruts vers leurs profils reconstruits vaut `0,163` en
  médiane et `1,027` au P95.

Ce passage ne porte pas encore sur le deck, la chambre, les conduits, les
sièges, les bougies ou la baie de distribution. Il ouvre uniquement la porte
`surface_reconstruction_scan_deviation_passed` et aucune porte de fabrication.

Le contrôle de packaging F40 charge dans cette enveloppe les dix groupes STEP
F38 : porte-axes, deux axes, quatre culbuteurs, quatre soupapes, quatre guides,
quatre sièges, huit ressorts et huit coupelles. Il affiche aussi les anciens Y
fluides F36 uniquement comme guide de position. La grande sphère de construction
de chambre F36 est explicitement exclue : la chambre F40 sera reconstruite
depuis le registre et la chambre visibles du scan, pas héritée d'un proxy.

Les commandes reproductibles sont :

```sh
make 917-f40-scan-locked-outer F40_PYTHON=/chemin/vers/python-avec-gmsh-ocp-trimesh
make 917-f40-4v-packaging F40_PYTHON=/chemin/vers/python-avec-gmsh-ocp-trimesh
make 917-f40-functional-trial F40_PYTHON=/chemin/vers/python-avec-manifold3d-trimesh
```

Les STEP et images issus du scan restent dans `work/917-f40-reference/`, hors
Git, conformément à la règle de provenance du scan.

## Essai fonctionnel maillé

Une première soustraction booléenne robuste a été exécutée dans l'enveloppe
F40 : noyau chambre/conduits en Y, douze volumes de passage pour tiges, guides
et sièges, deux pilotes de bougie, quatre passages de goujon et une baie de
distribution protégée autour des composants. Le résultat triangulé comporte
`387 604` faces, est étanche, cohérent en orientation et reconnu comme un seul
volume. Son volume vaut `1 051 403 unités³`, soit une masse indicative de
`2,870 kg` en CP1 si — et seulement si — l'unité OBJ est assimilée au
millimètre.

Ce résultat vérifie la topologie générale des ouvertures, pas la fabricabilité.
Il n'est pas un B-Rep fonctionnel éditable; les galeries d'huile, drains,
filetages, rayons de raccordement, surépaisseurs d'usinage et chaîne de cotes
restent absents. La masse est donc un indicateur de contrôle, pas une masse de
définition. Les portes d'impression métal et de démarrage moteur restent
fermées.

## Choix matière provisoire

Le matériau historique du moulage ne peut pas être déduit d'une photographie.
Pour la version LPBF, le candidat de travail reste EOS Aluminium Constellium CP1
(`AA8A61.50 / AMS 7074`, Al-Fe-Zr), et non du 2618 forgé artificiellement
transposé à l'impression. EOS publie un procédé M 290 à 60 micromètres, TRL 3,
avec traitement quatre heures à 400 °C; ces valeurs sont typiques et non des
valeurs admissibles de culasse. Le choix final reste conditionné aux coupons
chauds XY/Z déjà définis : traction, LCF, HCF, fluage, conductivité, dilatation,
densité, métallographie et CT.

## Matrice d'autorité

| Élément | Autorité retenue | Ce qui reste interdit |
| --- | --- | --- |
| peau, ailettes, bossages, position apparente des raccords | scan Wolfe local, SHA-256 verrouillé | remplacement par ellipse, boîte ou lissage global |
| hauteur et diamètres aux raccords | valeurs Retro Sport comme contrôles croisés | déduire les autres cotes depuis les pixels |
| architecture 917 historique | fiche FIA n° 250 | déclarer le scan identique à une culasse 917 |
| architecture 4V | géométrie nouvelle, calculée dans l'enveloppe conservée | la présenter comme historique ou homologuée Porsche |
| images commerciales | observation visuelle locale | copie ou redistribution dans Git |

## Reconstruction suivante

Le nouveau maître doit être produit par contours locaux du scan : sections
fermées, courbes B-spline, surfaces réglées ou loftées, puis raccords analytiques
pour les plans, alésages, sièges et guides. Les ailettes sont reconstruites
niveau par niveau; leur profil n'est pas remplacé par un rayon elliptique
commun. La carte d'écart doit être publiée au minimum avec moyenne, médiane,
P95, P99, maximum et une carte spatiale locale.

Les interfaces externes restent uniques. Les quatre soupapes reçoivent deux
Y internes continus, sans double bride ni double raccord ajouté. Les galeries
d'huile doivent être ouvertes vers un orifice de service et le dépoudrage doit
être démontré; aucune cavité fermée n'est admise.

## Portes de validation

F40 ne libère pas encore une impression ni un démarrage. Il faut encore :

1. reconstruire les surfaces fonctionnelles sur le B-Rep extérieur déjà passé ;
2. fermer la chaîne de cotes des surfaces fonctionnelles ;
3. vérifier l'épaisseur minimale de façon continue ;
4. exécuter CHT OpenFOAM et une contre-méthode indépendante sur la même pièce ;
5. résoudre la fatigue thermomécanique avec carte matière issue de coupons LPBF
   à chaud ;
6. calibrer la simulation de procédé, puis CT/CND, étanchéité, banc de flux et
   banc moteur ;
7. obtenir une revue et une libération professionnelles.

L'audit local reproductible se lance avec :

```sh
make 917-f40-935-scale-audit
```

Références :

- [Porsche 935, culasses TRW datées 10-78 — Retro Sport](https://retro-sport.com/products/porsche-race-cars/porsche-934-935/engine/porsche-935-cylinder-heads-with-new-trw-valves-set-of-6)
- [Porsche 935/78 « Moby Dick » — Porsche Newsroom](https://newsroom.porsche.com/de/pressemappen/Porsche-Museum/Porsche-935-78-%E2%80%9EMoby-Dick%E2%80%9C.html)
- [Historique Turbo et 935 — Porsche Newsroom DEU](https://newsroom.porsche.com/de/pressemappen/50-Jahre-Porsche-Turbo-36122/Die-Anf%C3%A4nge-und-die-Turbo-Technologie-im-Motorsport.html)
- [Catalogue Porsche Austauschprogramm Kat 097](https://www.porsche.at/media/Kwc_Basic_DownloadTag_Component/4740-45397-124836-downloadTag/default/9a180e6f/1733997420/kat097-d-atk-12-katalog.pdf)
- [Fiche FIA historique Porsche 917 n° 250](https://historicdb.fia.com/sites/default/files/car_attachment/1601078401/homologation_form_number_250_group_4.pdf)
- [Table de correspondance des culasses refroidies par air — LN Engineering](https://docs.lnengineering.com/article/35-aircooled-porsche-911-cylinder-head-part-number-cross-reference)
- [Culasse 935 NOS, référence moulée — Automobilia Ladenburg](https://www.automobilia-ladenburg.de/aAPI/catalogs/de/dc5ecd43cada9c9c4295b3da30cc2dc4/page/17?layout=print)
- [Fiche matériau CP1 et procédé M 290 — EOS](https://www.eos.info/metal-solutions/data-sheets/all-processes-and-materials?id=eos-aluminium-constellium-cp1)
