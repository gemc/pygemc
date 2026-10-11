<!-- TRANSLATIONS:START (managed by bin/translate) -->
**Languages:** [EN](README.md) · [IT](README.it.md) · [日本語](README.ja.md) · **FR** · [中文](README.zh.md)
<!-- TRANSLATIONS:END -->

# pygemc

[![Tests][tests-badge]][tests]
[![Python][python-badge]][pyproject]
[![PyPI][pypi-badge]][pypi]
[![Licence : Apache-2.0][license-badge]][license]
[![Documentation GEMC][docs-badge]][docs]
[![Téléchargements Docker][dockerhub-badge]][dockerhub]

`pygemc` est l'API Python utilisée par [GEMC](https://github.com/gemc/src) pour définir la géométrie des détecteurs,
les matériaux, les propriétés optiques, les miroirs et des processus légers d'analyse des résultats. Elle permet
de construire des bases de données GEMC avec des scripts Python, de prévisualiser la géométrie avec PyVista et
d'examiner les sorties GEMC au format CSV ou ROOT sans écrire de C++.

Le paquet s'installe avec pip ou lors de la compilation de GEMC à partir des sources. Il est aussi préinstallé
dans les images Docker de GEMC sur [Docker Hub](https://hub.docker.com/r/gemc/gemc) (et `ghcr.io/gemc/src`).

## Fonctionnalités

- Classes Python pour les bases de données de géométrie et de matériaux GEMC
- Fonctions utilitaires de `GVolume` pour les solides Geant4 courants : boîtes, tubes, cônes et trapézoïdes
- `GVolume.g4placement_type` pour choisir le constructeur actif ou passif de `G4Transform3D`
- Fonctions utilitaires de `GMaterial` pour les formules chimiques, les mélanges définis par fractions massiques et les propriétés optiques et de scintillation
- Gestion du run, de la variation, de la fabrique et des configurations SQLite, ASCII et PyVista par `GConfiguration`
- Configuration simplifiée avec `autogeometry()` pour les scripts de détecteurs
- Export des bases de données aux formats SQLite et ASCII
- Rendu PyVista, affichage interactif Qt et export VTK.js `.vtksz` pour l'inspection de la géométrie et la documentation
- Outil en ligne de commande `gemc-system-template` pour générer des systèmes de détecteurs prêts à être exécutés
- Extraits de code Python pour les constructeurs de solides Geant4 pris en charge
- Outil en ligne de commande `gemc-sqlite` pour créer et examiner les fichiers de bases de données SQLite de GEMC
- Outil en ligne de commande `gemc-cure-mesh` pour simplifier et réparer les maillages CAO (STL/PLY/OBJ) destinés aux solides tessellés de Geant4
- Outil en ligne de commande `gemc-analyzer` pour résumer et représenter graphiquement les sorties GEMC au format CSV ou ROOT
- Fonctions de conversion d'unités pour les chaînes représentant des longueurs, des angles, des durées et des énergies
- Suite de tests Pytest ne nécessitant pas de binaire `gemc` compilé

<br/>

# Installation

## Installation de la version stable depuis PyPI

Utilisez un environnement virtuel Python pour les installations directes via `pip`.
Sur macOS avec Homebrew, utilisez `/opt/homebrew/bin/python3` pour garantir l'utilisation du bon interpréteur :

```shell
/opt/homebrew/bin/python3 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
python -m pip install --upgrade pip
```

Installez [`pygemc` depuis PyPI](https://pypi.org/project/pygemc/) avec :

```shell
python -m pip install pygemc
```
Dépendances facultatives pour l'analyse des fichiers ROOT :

```shell
python -m pip install "pygemc[root]"
```


## Installation avec GEMC

Lorsque GEMC est compilé à partir des sources, pygemc est disponible dans vos scripts sans étape d'activation
ni installation pip distincte ; gemc et les outils Python sont également disponibles :

```shell
gemc -v
gemc-system-template --help
gemc-sqlite --help
gemc-analyzer --help
```

<br/>

# Démarrage rapide

Créez un modèle de détecteur :

```shell
gemc-system-template -s counter
cd counter
./counter.py
```

Le système généré contient :

| Fichier        | Rôle                                                 |
| -------------- | ---------------------------------------------------- |
| `counter.py`   | Script principal de construction de la géométrie      |
| `geometry.py`  | Volumes d'exemple, dont un détecteur de flux           |
| `materials.py` | Exemple de matériau : méthane gazeux                  |
| `counter.yaml` | Carte de pilotage GEMC                                |
| `README.md`    | Notes à compléter pour le détecteur généré            |

Exécutez le script avec la visualisation PyVista :

```shell
./counter.py -pv
```

Exportez une scène VTK.js :

```shell
./counter.py -pvvtk counter -pvz 0.25
```

Utilisez un fond clair et uni pour les exports destinés à la documentation :

```shell
./counter.py -pvvtk counter -pvbg "0.92 0.92 0.98" -pvbgt none
```

Exécutez la simulation générée avec GEMC lorsque l'exécutable `gemc` compilé est disponible :

```shell
gemc counter.yaml
```

Analysez la sortie :

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --bins 50
```

Les grandeurs pouvant être représentées sont les colonnes numériques du fichier chargé ; elles ne sont donc
connues qu'après la lecture des données et n'apparaissent pas dans `--help`. Exécutez l'analyseur avec seulement
un nom de fichier pour afficher le résumé, qui comprend le nombre de lignes et d'événements, si disponible,
ainsi que la liste `plottable <stream>: ...` pour chaque flux. L'option explicite `--list` affiche le même résumé :

```shell
gemc-analyzer counter_t0_digitized.csv
gemc-analyzer counter_t0_digitized.csv --list
```

À venir dans la prochaine version : les fichiers CSV de données de vérité de simulation contenant `pid`, `opid`
et les composantes actuelles et initiales de la quantité de mouvement donnent accès à `delta_p`, `delta_theta`
et `delta_phi`. Seules les lignes dont `pid` correspond à `opid` sont incluses dans ces graphiques ; `delta_phi`
est ramené à l'intervalle [-pi, pi]. Sélectionnez une espèce de particules avec `--pid`, par exemple
`gemc-analyzer hits_true_info.csv delta_p --pid 11`.

<br/>

# API de géométrie

Les scripts de géométrie créent généralement une configuration et y publient des volumes et des matériaux :

```python
from pygemc import GMaterial, GVolume, autogeometry

cfg = autogeometry("examples", "counter")

gas = GMaterial("methaneGas")
gas.description = "methane gas CH4 0.000667 g/cm3"
gas.density = 0.000667
gas.addNAtoms("C", 1)
gas.addNAtoms("H", 4)
gas.publish(cfg)

flux = GVolume("flux_box")
flux.description = "air flux box"
flux.make_box(40.0, 40.0, 2.0)
flux.set_position(0, 0, 100)
flux.material = "G4_AIR"
flux.color = "3399FF"
flux.style = 1
flux.digitization = "flux"
flux.set_identifier("box", 2)
flux.publish(cfg)
```

## Convention de placement

`GVolume.g4placement_type` sélectionne la convention de placement Geant4 que GEMC doit utiliser pour un volume :

| Valeur    | Signification                                                                            |
| --------- | ---------------------------------------------------------------------------------------- |
| `active`  | Par défaut ; utilise `G4Transform3D(rotation, translation)`                                |
| `passive` | Utilise `G4PVPlacement(rotation, translation, ...)`, selon les conventions GEMC2/clas12Tags |

La plupart des nouvelles géométries GEMC3 peuvent utiliser la convention `active` par défaut. Les systèmes de
détecteurs portés depuis GEMC2 qui reposent sur des rotations de repère doivent définir :

```python
gvolume.g4placement_type = "passive"
```

Ce champ est écrit dans les bases de données de géométrie SQLite. La colonne manquante est ajoutée aux bases
de données SQLite existantes lorsqu'un script de géométrie publie de nouvelles lignes.

Options de ligne de commande courantes acceptées par les scripts de géométrie :

| Option                       | Rôle                                                                           |
|------------------------------|--------------------------------------------------------------------------------|
| `-f`, `--factory`            | Sélectionner le format de sortie `sqlite` ou `ascii`                            |
| `-v`, `--variation`          | Sélectionner la variation de géométrie                                         |
| `-r`, `--run`                | Sélectionner le numéro de run                                                  |
| `-sql`, `--dbhost`           | Sélectionner le chemin du fichier SQLite                                       |
| `-pv`                        | Afficher une fenêtre PyVista                                                   |
| `-pvb`                       | Afficher une fenêtre de rendu PyVistaQt en arrière-plan                        |
| `-pvvtk`                     | Exporter une scène VTK.js `.vtksz`                                             |
| `-pvz`                       | Régler le zoom de l'export VTK.js                                               |
| `--pyvista-variation NAME`   | Afficher une seule variation dans PyVista ; par défaut, la première variation rendue |
| `--pyvista-fast`             | Regrouper les volumes PyVista en moins d'acteurs pour accélérer le rendu des grandes géométries |
| `--no-pyvista-fast`          | Désactiver le regroupement automatique PyVista                                 |
| `--pyvista-fast-threshold N` | Activer automatiquement le regroupement PyVista au-delà de `N` volumes rendus  |
| `-pvbg`                      | Définir la couleur de fond PyVista par un nom, une chaîne hexadécimale ou un triplet `r g b` |
| `-pvbgt`                     | Définir la couleur facultative du haut du dégradé de fond PyVista ; utiliser `none` pour un fond uni |
| `--read-yaml`                | Lire la direction `g4camera` et les réglages `g4view.background` depuis un fichier YAML GEMC |

## Visualisation PyVista

La prise en charge de PyVista est au cœur de `pygemc` : les scripts de géométrie peuvent afficher le détecteur
à mesure qu'ils le construisent, ouvrir une visionneuse Qt interactive ou exporter une scène `.vtksz` pouvant
être publiée dans la documentation.

<table>
  <tr>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/b1/b1.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/b1/gemc_view.png"
             alt="B1 PyVista" width="180"><br>
        B1
      </a>
    </td>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/b2/b2.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/b2/gemc_view.png"
             alt="B2 PyVista" width="180"><br>
        B2
      </a>
    </td>
  </tr>
  <tr>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/materials/material.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/materials/gemc_view.png"
             alt="Materials PyVista" width="180"><br>
        Matériaux
      </a>
    </td>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/scintillator_barrel/scintillator_barrel.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/scintillator_barrel/gemc_view.png"
             alt="Scintillator Barrel PyVista" width="180"><br>
        Détecteur à scintillation en tonneau
      </a>
    </td>
  </tr>
</table>

Ouvrez les scènes PyVista interactives générées à partir des exemples GEMC en suivant les liens.

Les pages README de GitHub ne peuvent pas intégrer directement les fichiers `.vtksz` ; l'image d'aperçu
renvoie donc vers la visionneuse VTK.js hébergée.

## Outils en ligne de commande

<table>
  <thead>
    <tr>
      <th>Commande</th>
      <th>Fonction</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -s counter</code></td>
      <td>Générer un squelette de détecteur nommé <code>counter</code>.</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -sl</code></td>
      <td>Lister les extraits de code pour les solides Geant4 pris en charge.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -gv G4Box</code></td>
      <td>Afficher un extrait de code de construction de volume pour un <code>G4Box</code>.</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -gv G4Tubs -write_to geometry.py -geo_sub build_tube</code></td>
      <td>Écrire un extrait de code pour <code>G4Tubs</code> dans <code>geometry.py</code>.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -n mydetector.sqlite</code></td>
      <td>Créer une base de données SQLite avec le schéma GEMC pour la géométrie et les matériaux.</td>
    </tr>
    <tr>
      <td><code>gemc-sqlite -sql mydetector.sqlite -sv</code></td>
      <td>Ouvrir une base de données existante et lister ses volumes.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -sql mydetector.sqlite -sm</code></td>
      <td>Ouvrir une base de données existante et lister ses matériaux.</td>
    </tr>
    <tr>
      <td>
        <code>gemc-sqlite -sql mydetector.sqlite -sv -ef examples -vf default -sf counter -rf 1</code>
      </td>
      <td>Filtrer les volumes listés par expérience, variation, système et numéro de run.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-cure-mesh organ.stl -o organ.stl -f 15000</code></td>
      <td>Simplifier et réparer un maillage CAO (réduction à environ 15 000 facettes, fusion des sommets, fermeture des trous, réorientation) pour Geant4.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-analyzer counter_t0_digitized.csv</code></td>
      <td>Résumer un fichier de sortie GEMC au format CSV et lister les grandeurs à tracer pour chaque flux.</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer counter_t0_digitized.csv totEdep --bins 50</code></td>
      <td>Tracer une variable numérisée avec 50 classes d'histogramme.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td>
        <code>
          gemc-analyzer counter_t0_true_info.csv --plot yvsx --xlim -20 20 --ylim -20 20
        </code>
      </td>
      <td>Tracer les positions des impacts issues de la vérité de simulation dans le plan y en fonction de x.</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer out.root E --detector flux --save energy.png</code></td>
      <td>Enregistrer une figure de l'analyseur à partir de données ROOT sans ouvrir d'interface graphique.</td>
    </tr>
  </tbody>
</table>

## Tests

Exécutez les tests Python autonomes :

```shell
pytest
pytest tests/test_analyzer.py
pytest tests/test_cli.py
pytest tests/test_gconfiguration_yaml.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

Les tests couvrent les tracés de l'analyseur, le comportement des outils en ligne de commande, la configuration
PyVista pilotée par YAML et la génération de bases de données de géométrie. Ils sont conçus pour ne nécessiter
ni Geant4 ni exécutable `gemc` compilé ; les tests de simulation complets font partie du système de compilation
meson du projet GEMC parent.

## Organisation du projet

| Chemin                 | Rôle                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `src/pygemc/api/`      | Géométrie, matériaux, unités, sortie SQLite, prise en charge PyVista et modèles |
| `src/pygemc/analyzer/` | Lecteurs CSV/ROOT, tracés et outil d'analyse en ligne de commande           |
| `tests/`               | Suite pytest autonome                                                     |
| `.github/workflows/`   | Workflows de CI, de création de versions, de publication PyPI et d'intégration GEMC |
| `releases/`            | Notes de version                                                          |
| `pyproject.toml`       | Métadonnées de distribution Python et scripts de console                   |
| `meson.build`          | Intégration du sous-projet meson utilisée par GEMC                          |

## Documentation

- [Guide des workflows CI](.github/workflows/README.md)
- [Page d'accueil de GEMC](https://gemc.github.io/home/)
- [Vue d'ensemble de l'API Python](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [Démarrage rapide](https://gemc.github.io/home/documentation/quickstart/)
- [Exemples](https://gemc.github.io/home/examples/)
- [Dépôt source de GEMC](https://github.com/gemc/src)
- [Dépôt des systèmes GEMC pour CLAS12](https://github.com/gemc/clas12-systems)
- [Dépôt du site web de documentation](https://github.com/gemc/home)
- [Dépôt GEMC2 / CLAS12](https://github.com/gemc/clas12Tags)

## Contribuer

Gardez les correctifs ciblés et exécutez les cibles pytest pertinentes avant d'ouvrir une demande de fusion.
Si une modification affecte la compilation intégrée de GEMC, exécutez également les tests meson du dépôt
parent pour les exemples ou modules concernés.

## Licence

`pygemc` est distribué sous la [licence Apache, version 2.0](LICENSE), également utilisée par le dépôt source
principal de GEMC. Consultez [`NOTICE`](NOTICE) pour les mentions d'attribution.

[tests]: https://github.com/gemc/pygemc/actions/workflows/pygemc_tests.yml
[tests-badge]: https://github.com/gemc/pygemc/actions/workflows/pygemc_tests.yml/badge.svg
[python-badge]: https://img.shields.io/badge/python-3.10%2B-blue.svg
[pypi]: https://pypi.org/project/pygemc/
[pypi-badge]: https://img.shields.io/pypi/v/pygemc.svg?cacheSeconds=300
[license]: LICENSE
[license-badge]: https://img.shields.io/badge/license-Apache--2.0-blue.svg
[docs]: https://gemc.github.io/home/
[docs-badge]: https://img.shields.io/badge/docs-gemc.github.io-blue.svg
[pyproject]: pyproject.toml
[dockerhub]: https://hub.docker.com/r/gemc/gemc
[dockerhub-badge]: https://img.shields.io/docker/pulls/gemc/gemc.svg
