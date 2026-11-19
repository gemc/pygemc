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

`pygemc` est l'API Python utilisée par [GEMC](https://github.com/gemc/src) pour définir la géométrie des détecteurs, les matériaux, les propriétés optiques, les miroirs,
et des procédures légères d'analyse des sorties. Elle permet de créer des bases de données GEMC avec des scripts Python, de prévisualiser la géométrie
avec PyVista et d'inspecter les sorties CSV ou ROOT de GEMC sans écrire de C++.

Le paquet s'installe avec pip ou lors de la compilation des sources de GEMC. Il est également préinstallé dans les images
Docker de GEMC sur [Docker Hub](https://hub.docker.com/r/gemc/gemc) (et `ghcr.io/gemc/src`).

## Fonctionnalités

- Classes Python pour les bases de données de géométrie et de matériaux GEMC
- Méthodes utilitaires de `GVolume` pour les solides Geant4 courants : boîtes, tubes, cônes et trapézoïdes
- `GVolume.g4placement_type` pour sélectionner le constructeur actif ou passif de `G4Transform3D`
- Méthodes utilitaires de `GMaterial` pour les formules chimiques, les mélanges définis par fractions massiques et les propriétés optiques et de scintillation
- Gestion par `GConfiguration` du run, de la variation, de la fabrique et des paramètres SQLite, ASCII et PyVista
- Configuration simplifiée avec `autogeometry()` pour les scripts de détecteurs
- Production de bases de données SQLite et ASCII
- Rendu PyVista, affichage Qt interactif et export VTK.js `.vtksz` pour l'inspection de la géométrie et la documentation
- Interface en ligne de commande `gemc-system-template` pour générer des systèmes de détecteurs prêts à l'emploi
- Extraits de code Python pour les constructeurs de solides Geant4 pris en charge
- Interface en ligne de commande `gemc-sqlite` pour créer et inspecter les fichiers de bases de données SQLite de GEMC
- Interface en ligne de commande `gemc-cure-mesh` pour simplifier et réparer les maillages CAO (STL/PLY/OBJ) destinés aux solides tessellés de Geant4
- Interface en ligne de commande `gemc-analyzer` pour résumer et représenter graphiquement les sorties CSV ou ROOT de GEMC
- Fonctions de conversion d'unités pour les chaînes représentant des longueurs, des angles, des temps et des énergies
- Suite de tests Pytest ne nécessitant pas de binaire `gemc` compilé

<br/>

# Installation

pygemc s'installe selon l'un des deux modes suivants ; choisissez celui qui convient à votre usage :

- **`latest`** — la version publiée sur PyPI. C'est le mode par défaut, adapté à la plupart des utilisateurs.
- **`dev`** — une installation éditable de cette arborescence source, pour développer ou tester pygemc lui-même.

Sélectionnez le mode en choisissant la commande `pip` dans votre environnement virtuel :

```shell
python -m pip install pygemc        # latest: the stable release from PyPI
python -m pip install -e ".[dev]"   # dev: editable checkout, run from the repository root
```

Les sections [Installation stable depuis PyPI](#stable-pypi-install-latest) et [Tests](#tests) détaillent chacune des deux approches.

## Installation stable depuis PyPI (`latest`)

Utilisez Python 3.10-3.14 dans un environnement virtuel pour les installations directes via `pip`. La borne supérieure de cette plage
sera prise en charge dans la prochaine version ; `pymeshlab` reste une dépendance obligatoire.
Sous macOS avec Homebrew, installez et sélectionnez explicitement Python 3.14 :

```shell
brew install python@3.14
/opt/homebrew/bin/python3.14 -m venv ~/venv/pygemc
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

À venir dans la prochaine version : pygemc gère les environnements Python pour GEMC et les systèmes CLAS12.
Son sous-projet Meson sélectionne Python 3.10-3.14, crée l'environnement de compilation et enregistre le
mécanisme d'installation qui installe pygemc et ses dépendances sous `<prefix>/python_env`.
Les deux projets qui l'utilisent emploient l'interpréteur exporté pour la compilation.

Après avoir ajouté `<prefix>/bin` et `<prefix>/python_env/bin` à `PATH`, GEMC et les outils Python sont disponibles :

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

| Fichier        | Rôle                                            |
| -------------- | ----------------------------------------------- |
| `counter.py`   | Script principal de construction de la géométrie |
| `geometry.py`  | Exemples de volumes, dont un détecteur de flux   |
| `materials.py` | Exemple de matériau : méthane gazeux            |
| `counter.yaml` | Fichier de pilotage GEMC                        |
| `README.md`    | Notes à compléter pour le détecteur généré      |

Exécutez le script avec la visualisation PyVista :

```shell
./counter.py -pv
```

Exportez une scène VTK.js :

```shell
./counter.py -pvvtk counter -pvz 0.25
```

Utilisez un arrière-plan clair et uni pour les exports destinés à la documentation :

```shell
./counter.py -pvvtk counter -pvbg "0.92 0.92 0.98" -pvbgt none
```

Lancez la simulation générée avec GEMC lorsque l'exécutable `gemc` compilé est disponible :

```shell
gemc counter.yaml
```

Analysez la sortie :

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --bins 50
```

Les grandeurs pouvant être représentées sont les colonnes numériques du fichier chargé ; elles ne sont donc connues qu'après
la lecture des données et n'apparaissent pas dans `--help`. Exécutez l'analyseur avec uniquement un nom de fichier pour afficher le résumé,
qui comprend les nombres de lignes et d'événements lorsqu'ils sont disponibles, ainsi que la liste `plottable <stream>: ...` pour chaque flux.
L'option explicite `--list` affiche le même résumé :

```shell
gemc-analyzer counter_t0_digitized.csv
gemc-analyzer counter_t0_digitized.csv --list
```

À venir dans la prochaine version : les fichiers CSV de données de vérité de simulation contenant `pid`, `opid` ainsi que les composantes
de la quantité de mouvement courante et d'origine donnent accès à `delta_p`, `delta_theta` et `delta_phi`. Seules les lignes dont `pid` est égal à `opid` sont incluses
dans ces graphiques ; `delta_phi` est replié dans l'intervalle [-pi, pi]. Sélectionnez une espèce de particules avec `--pid`, par
exemple `gemc-analyzer hits_true_info.csv delta_p --pid 11`.

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
| `active`  | Valeur par défaut ; utilise `G4Transform3D(rotation, translation)`                         |
| `passive` | Utilise `G4PVPlacement(rotation, translation, ...)`, conformément aux conventions GEMC2/clas12Tags |

La plupart des nouvelles géométries GEMC3 peuvent utiliser la convention `active` par défaut. Les systèmes de détecteurs portés depuis GEMC2
qui reposent sur des rotations de repère doivent définir :

```python
gvolume.g4placement_type = "passive"
```

Ce champ est enregistré dans les bases de données de géométrie SQLite. La colonne manquante est ajoutée aux bases de données
SQLite existantes lorsqu'un script de géométrie publie de nouvelles lignes.

Les placements CAO peuvent être publiés via la même configuration (à venir dans la prochaine version) :

```python
from pygemc import build_cad

build_cad(cfg, "cad/cad_default.gxml", cad_dir="stls", passive=True)
build_cad(cfg, "stls/cad__default.yaml", passive=True)
```

Cette fonction utilitaire accepte les descriptions de placement en GXML, YAML, JSON ou sous forme de tables de correspondance Python, et utilise
le système, la variation, le run et le format de sortie courants de la configuration. Elle préserve les banques existantes. Les chemins et facteurs d'échelle des maillages, les placements `copyOf`,
les matériaux, les revêtements optiques et les champs de lecture sont traités de la même manière qu'avec `gemc-sqlite -cad`.
Utilisez `passive=True` pour les rotations de repère GEMC2. `defaults` fournit les champs communs aux volumes et
`material_aliases` associe les noms des matériaux sources aux noms utilisés à l'exécution. Les calculs de placement propres à chaque détecteur
restent dans les scripts du détecteur et peuvent transmettre leurs résultats sous forme de liste de tables de correspondance.

Options de ligne de commande courantes acceptées par les scripts de géométrie :

| Option                       | Rôle                                                                           |
|------------------------------|--------------------------------------------------------------------------------|
| `-f`, `--factory`            | Sélectionner la sortie `sqlite` ou `ascii`                                      |
| `-v`, `--variation`          | Sélectionner la variation de géométrie                                          |
| `-r`, `--run`                | Sélectionner le numéro de run                                                   |
| `-sql`, `--dbhost`           | Sélectionner le chemin du fichier SQLite                                        |
| `-pv`                        | Afficher une fenêtre PyVista                                                   |
| `-pvb`                       | Afficher une fenêtre de visualisation PyVistaQt en arrière-plan                 |
| `-pvvtk`                     | Exporter une scène VTK.js `.vtksz`                                              |
| `-pvz`                       | Définir le zoom de l'export VTK.js                                              |
| `--pyvista-variation NAME`   | Afficher une seule variation dans PyVista ; par défaut, la première variation rendue |
| `--pyvista-fast`             | Regrouper les volumes PyVista en un nombre réduit d'acteurs pour accélérer le rendu des grandes géométries |
| `--no-pyvista-fast`          | Désactiver le regroupement automatique des volumes PyVista                      |
| `--pyvista-fast-threshold N` | Activer automatiquement le regroupement PyVista au-delà de `N` volumes rendus   |
| `-pvbg`                      | Définir la couleur d'arrière-plan PyVista par un nom, une chaîne hexadécimale ou un triplet `r g b` |
| `-pvbgt`                     | Définir la couleur facultative du haut du dégradé PyVista ; utiliser `none` pour un arrière-plan uni |
| `--read-yaml`                | Lire la direction `g4camera` et les paramètres `g4view.background` depuis un fichier YAML GEMC |

## Visualisation PyVista

La prise en charge de PyVista est au cœur de `pygemc` : les scripts de géométrie peuvent afficher le détecteur au fil de sa construction,
ouvrir une visionneuse Qt interactive ou exporter une scène `.vtksz` pouvant être publiée dans la documentation.

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
        Tonneau de scintillateurs
      </a>
    </td>
  </tr>
</table>

Ouvrez les scènes PyVista interactives accessibles par ces liens, générées à partir des exemples GEMC.

Les pages README de GitHub ne peuvent pas intégrer directement les fichiers `.vtksz` ; l'image d'aperçu renvoie donc vers la visionneuse VTK.js hébergée.

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
      <td>Lister les extraits de code disponibles pour les solides Geant4 pris en charge.</td>
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
      <td>Créer une nouvelle base de données SQLite avec le schéma de géométrie et de matériaux de GEMC.</td>
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
      <td>Simplifier et réparer un maillage CAO (réduire à environ 15 000 facettes, fusionner les sommets, fermer les trous, réorienter les facettes) pour Geant4.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-analyzer counter_t0_digitized.csv</code></td>
      <td>Résumer un fichier de sortie CSV de GEMC et lister les grandeurs pouvant être représentées pour chaque flux.</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer counter_t0_digitized.csv totEdep --bins 50</code></td>
      <td>Tracer l'histogramme d'une variable numérisée avec 50 classes.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td>
        <code>
          gemc-analyzer counter_t0_true_info.csv --plot yvsx --xlim -20 20 --ylim -20 20
        </code>
      </td>
      <td>Tracer les positions simulées des impacts, y en fonction de x.</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer out.root E --detector flux --save energy.png</code></td>
      <td>Enregistrer une figure de l'analyseur à partir de données ROOT sans ouvrir d'interface graphique.</td>
    </tr>
  </tbody>
</table>

## Tests

Installez le paquet en mode éditable (le mode d'installation `dev`) avec ses dépendances de développement (`pytest`,
`pytest-cov`, `ruff`). L'installation éditable permet également à `pytest` d'importer les sources `src/pygemc` de l'arborescence locale plutôt
qu'un paquet wheel de PyPI précédemment installé, qui masquerait ces sources et empêcherait la collecte des tests :

```shell
python -m pip install -e ".[dev]"
```

Exécutez ensuite les tests Python autonomes :

```shell
pytest
pytest tests/test_analyzer.py
pytest tests/test_cli.py
pytest tests/test_gconfiguration_yaml.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

Les tests couvrent les tracés de l'analyseur, le comportement de l'interface en ligne de commande, la configuration PyVista pilotée par YAML et la génération
des bases de données de géométrie. Ils sont conçus pour ne nécessiter ni Geant4 ni exécutable `gemc` compilé ; les tests de simulation complets
font partie du système de compilation Meson du dépôt GEMC parent.

## Organisation du projet

| Chemin                 | Rôle                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `src/pygemc/api/`      | Géométrie, matériaux, unités, sortie SQLite, prise en charge de PyVista et modèles |
| `src/pygemc/analyzer/` | Lecteurs CSV/ROOT, tracés et interface en ligne de commande de l'analyseur |
| `tests/`               | Suite pytest autonome                                                     |
| `.github/workflows/`   | Workflows d'intégration continue, de livraison de versions, de publication sur PyPI et d'intégration GEMC |
| `releases/`            | Notes de version                                                          |
| `pyproject.toml`       | Métadonnées de création du paquet Python et scripts de console             |
| `meson.build`          | Intégration du sous-projet Meson utilisée par GEMC                         |

## Documentation

- [Guide des workflows d'intégration continue](.github/workflows/README.md)
- [Page d'accueil de GEMC](https://gemc.github.io/home/)
- [Présentation de l'API Python](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [Démarrage rapide](https://gemc.github.io/home/documentation/quickstart/)
- [Exemples](https://gemc.github.io/home/examples/)
- [Dépôt des sources de GEMC](https://github.com/gemc/src)
- [Dépôt des systèmes GEMC pour CLAS12](https://github.com/gemc/clas12-systems)
- [Dépôt du site web de documentation](https://github.com/gemc/home)
- [Dépôt GEMC2 / CLAS12](https://github.com/gemc/clas12Tags)

## Contribuer

Limitez chaque correctif à un objectif précis et exécutez les cibles pytest pertinentes avant d'ouvrir une pull request. Si une modification affecte la compilation intégrée de GEMC, exécutez également les tests Meson du dépôt parent pour les exemples ou modules concernés.

## Licence

`pygemc` est distribué sous la [licence Apache, version 2.0](LICENSE) — la même licence que celle utilisée par le dépôt principal
des sources de GEMC. Consultez [`NOTICE`](NOTICE) pour les mentions d'attribution.

[tests]: https://github.com/gemc/pygemc/actions/workflows/pygemc_tests.yml
[tests-badge]: https://github.com/gemc/pygemc/actions/workflows/pygemc_tests.yml/badge.svg
[python-badge]: https://img.shields.io/badge/python-3.10%E2%80%933.14-blue.svg
[pypi]: https://pypi.org/project/pygemc/
[pypi-badge]: https://img.shields.io/pypi/v/pygemc.svg?cacheSeconds=300
[license]: LICENSE
[license-badge]: https://img.shields.io/badge/license-Apache--2.0-blue.svg
[docs]: https://gemc.github.io/home/
[docs-badge]: https://img.shields.io/badge/docs-gemc.github.io-blue.svg
[pyproject]: pyproject.toml
[dockerhub]: https://hub.docker.com/r/gemc/gemc
[dockerhub-badge]: https://img.shields.io/docker/pulls/gemc/gemc.svg
