<!-- TRANSLATIONS:START (managed by bin/translate) -->
**Languages:** [EN](README.md) · **IT** · [日本語](README.ja.md) · [FR](README.fr.md) · [中文](README.zh.md)
<!-- TRANSLATIONS:END -->

# pygemc

[![Test][tests-badge]][tests]
[![Python][python-badge]][pyproject]
[![PyPI][pypi-badge]][pypi]
[![Licenza: Apache-2.0][license-badge]][license]
[![Documentazione GEMC][docs-badge]][docs]
[![Pull Docker][dockerhub-badge]][dockerhub]

`pygemc` è l'API Python usata da [GEMC](https://github.com/gemc/src) per definire geometrie di rivelatori, materiali, proprietà ottiche, specchi,
e flussi di lavoro leggeri per l'analisi dell'output. Consente di costruire database GEMC con script Python, visualizzare la geometria in anteprima
con PyVista e ispezionare l'output CSV o ROOT di GEMC senza scrivere C++.

Il pacchetto si installa con pip o durante la compilazione di GEMC dai sorgenti. È inoltre preinstallato nelle
immagini Docker di GEMC su [Docker Hub](https://hub.docker.com/r/gemc/gemc) (e `ghcr.io/gemc/src`).

## Funzionalità

- Classi Python per i database di geometria e materiali di GEMC
- Metodi di supporto di `GVolume` per solidi Geant4 comuni come parallelepipedi, tubi, coni e trapezoidi
- `GVolume.g4placement_type` per selezionare il costruttore attivo o passivo di `G4Transform3D`
- Metodi di supporto di `GMaterial` per formule chimiche, miscele con frazioni massiche e proprietà ottiche/di scintillazione
- Gestione con `GConfiguration` delle impostazioni di run, variante, factory, SQLite, ASCII e PyVista
- Configurazione semplificata con `autogeometry()` per gli script dei rivelatori
- Output su database SQLite e ASCII
- Rendering con PyVista, visualizzazione interattiva con Qt ed esportazione VTK.js `.vtksz` per ispezione e documentazione
- CLI `gemc-system-template` per generare sistemi di rivelatori pronti all'uso
- Frammenti di codice Python per i costruttori di solidi Geant4 supportati
- CLI `gemc-sqlite` per creare e ispezionare file di database SQLite di GEMC
- CLI `gemc-cure-mesh` per semplificare e riparare mesh CAD (STL/PLY/OBJ) per i solidi tassellati di Geant4
- CLI `gemc-analyzer` per riepilogare e rappresentare graficamente l'output CSV o ROOT di GEMC
- Funzioni di supporto per convertire le unità nelle stringhe che esprimono lunghezza, angolo, tempo ed energia
- Suite Pytest che non richiede un eseguibile `gemc` compilato

<br/>

# Installazione

## Installazione della versione stabile da PyPI

Usa un ambiente virtuale Python per le installazioni dirette con `pip`.
Su macOS con Homebrew usa `/opt/homebrew/bin/python3` per assicurarti che venga utilizzato l'interprete corretto:

```shell
/opt/homebrew/bin/python3 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
python -m pip install --upgrade pip
```

Installa [`pygemc` da PyPI](https://pypi.org/project/pygemc/) con:

```shell
python -m pip install pygemc
```
Dipendenze opzionali per l'analisi dei file ROOT:

```shell
python -m pip install "pygemc[root]"
```


## Installazione con GEMC

Quando GEMC viene compilato dai sorgenti, pygemc è disponibile negli script senza
alcun passaggio di attivazione o installazione separata con pip; sono disponibili anche gemc e gli strumenti Python:

```shell
gemc -v
gemc-system-template --help
gemc-sqlite --help
gemc-analyzer --help
```

<br/>

# Avvio rapido

Crea un modello di rivelatore:

```shell
gemc-system-template -s counter
cd counter
./counter.py
```

Il sistema generato contiene:

| File           | Scopo                                      |
| -------------- | -------------------------------------------- |
| `counter.py`   | Script principale per la costruzione della geometria |
| `geometry.py`  | Volumi di esempio, incluso un rivelatore di flusso |
| `materials.py` | Materiale di esempio costituito da gas metano |
| `counter.yaml` | Scheda di configurazione di GEMC |
| `README.md`    | Note segnaposto per il rivelatore generato |

Esegui con la visualizzazione PyVista:

```shell
./counter.py -pv
```

Esporta una scena VTK.js:

```shell
./counter.py -pvvtk counter -pvz 0.25
```

Usa uno sfondo chiaro e uniforme per le esportazioni destinate alla documentazione:

```shell
./counter.py -pvvtk counter -pvbg "0.92 0.92 0.98" -pvbgt none
```

Esegui la simulazione generata con GEMC quando è disponibile l'eseguibile `gemc` compilato:

```shell
gemc counter.yaml
```

Analizza l'output:

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --bins 50
```

Le grandezze rappresentabili graficamente sono le colonne numeriche del file caricato, quindi sono note solo dopo
la lettura dei dati e non compaiono in `--help`. Esegui l'analizzatore con il solo nome del file per stampare il riepilogo,
inclusi i conteggi di righe ed eventi, se disponibili, e l'elenco `plottable <stream>: ...` per ciascun flusso.
L'opzione esplicita `--list` stampa lo stesso riepilogo:

```shell
gemc-analyzer counter_t0_digitized.csv
gemc-analyzer counter_t0_digitized.csv --list
```

In arrivo nella prossima versione: i file CSV con informazioni di verità contenenti `pid`, `opid` e le componenti
della quantità di moto attuale e originaria rendono disponibili `delta_p`, `delta_theta` e `delta_phi`. Questi grafici
includono solo le righe in cui `pid` coincide con `opid`; `delta_phi` è ricondotto all'intervallo [-pi, pi]. Seleziona
una sola specie di particella con `--pid`, ad esempio `gemc-analyzer hits_true_info.csv delta_p --pid 11`.

<br/>

# API di geometria

Gli script di geometria tipici creano una configurazione e vi pubblicano volumi e materiali:

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

## Convenzione di posizionamento

`GVolume.g4placement_type` seleziona la convenzione di posizionamento Geant4 che GEMC deve usare per un volume:

| Valore    | Significato                                                                                  |
| --------- | ---------------------------------------------------------------------------------------- |
| `active`  | Predefinito; usa `G4Transform3D(rotation, translation)` |
| `passive` | Usa `G4PVPlacement(rotation, translation, ...)`, conformemente alle convenzioni GEMC2/clas12Tags |

La maggior parte delle nuove geometrie GEMC3 può usare la convenzione predefinita `active`. I sistemi di rivelatori
migrati da GEMC2 che si basano su rotazioni del sistema di riferimento dovrebbero impostare:

```python
gvolume.g4placement_type = "passive"
```

Questo campo viene scritto nei database di geometria SQLite. La colonna mancante viene aggiunta ai database SQLite
esistenti quando uno script di geometria pubblica nuove righe.

Opzioni comuni da riga di comando accettate dagli script di geometria:

| Opzione                       | Scopo                                                                        |
|------------------------------|--------------------------------------------------------------------------------|
| `-f`, `--factory`            | Seleziona l'output `sqlite` o `ascii` |
| `-v`, `--variation`          | Seleziona la variante della geometria |
| `-r`, `--run`                | Seleziona il numero di run |
| `-sql`, `--dbhost`           | Seleziona il percorso del file SQLite |
| `-pv`                        | Mostra una finestra PyVista |
| `-pvb`                       | Mostra un plotter PyVistaQt in background |
| `-pvvtk`                     | Esporta una scena VTK.js `.vtksz` |
| `-pvz`                       | Imposta lo zoom dell'esportazione VTK.js |
| `--pyvista-variation NAME`   | Visualizza una sola variante in PyVista; per impostazione predefinita, la prima visualizzata |
| `--pyvista-fast`             | Raggruppa i volumi PyVista in meno attori per accelerare il rendering di geometrie grandi |
| `--no-pyvista-fast`          | Disabilita il raggruppamento automatico di PyVista |
| `--pyvista-fast-threshold N` | Abilita automaticamente il raggruppamento PyVista oltre `N` volumi visualizzati |
| `-pvbg`                      | Imposta il colore di sfondo di PyVista come nome, stringa esadecimale o terna `r g b` |
| `-pvbgt`                     | Imposta il colore superiore opzionale del gradiente PyVista; usa `none` per uno sfondo uniforme |
| `--read-yaml`                | Legge la direzione `g4camera` e le impostazioni `g4view.background` da un file YAML di GEMC |

## Visualizzazione PyVista

Il supporto a PyVista è centrale in `pygemc`: gli script di geometria possono mostrare il rivelatore mentre lo costruiscono,
aprire un visualizzatore Qt interattivo o esportare una scena `.vtksz` pubblicabile nella documentazione.

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
        Materiali
      </a>
    </td>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/scintillator_barrel/scintillator_barrel.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/scintillator_barrel/gemc_view.png"
             alt="Scintillator Barrel PyVista" width="180"><br>
        Barrel di scintillatori
      </a>
    </td>
  </tr>
</table>

Apri tramite i collegamenti le scene PyVista interattive generate dagli esempi di GEMC.

Le pagine README di GitHub non possono incorporare direttamente file `.vtksz`, quindi l'anteprima rimanda al visualizzatore VTK.js ospitato online.

## Strumenti da riga di comando

<table>
  <thead>
    <tr>
      <th>Comando</th>
      <th>Funzione</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -s counter</code></td>
      <td>Genera la struttura di base di un rivelatore chiamato <code>counter</code>.</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -sl</code></td>
      <td>Elenca i frammenti di codice per i solidi Geant4 supportati.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -gv G4Box</code></td>
      <td>Stampa un frammento di codice per costruire un volume <code>G4Box</code>.</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -gv G4Tubs -write_to geometry.py -geo_sub build_tube</code></td>
      <td>Scrive un frammento di codice per <code>G4Tubs</code> in <code>geometry.py</code>.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -n mydetector.sqlite</code></td>
      <td>Crea un nuovo database SQLite con lo schema GEMC per geometria e materiali.</td>
    </tr>
    <tr>
      <td><code>gemc-sqlite -sql mydetector.sqlite -sv</code></td>
      <td>Apre un database esistente e ne elenca i volumi.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -sql mydetector.sqlite -sm</code></td>
      <td>Apre un database esistente e ne elenca i materiali.</td>
    </tr>
    <tr>
      <td>
        <code>gemc-sqlite -sql mydetector.sqlite -sv -ef examples -vf default -sf counter -rf 1</code>
      </td>
      <td>Filtra i volumi elencati per esperimento, variante, sistema e numero di run.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-cure-mesh organ.stl -o organ.stl -f 15000</code></td>
      <td>Semplifica e ripara una mesh CAD per Geant4 (riduce a circa 15.000 facce, salda, chiude fori, riorienta).</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-analyzer counter_t0_digitized.csv</code></td>
      <td>Riepiloga un file CSV di output GEMC ed elenca le grandezze rappresentabili graficamente per ciascun flusso.</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer counter_t0_digitized.csv totEdep --bins 50</code></td>
      <td>Rappresenta graficamente una variabile digitalizzata con 50 bin.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td>
        <code>
          gemc-analyzer counter_t0_true_info.csv --plot yvsx --xlim -20 20 --ylim -20 20
        </code>
      </td>
      <td>Rappresenta le posizioni vere degli hit nel piano y rispetto a x.</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer out.root E --detector flux --save energy.png</code></td>
      <td>Salva una figura dell'analizzatore basata su dati ROOT senza aprire un'interfaccia grafica.</td>
    </tr>
  </tbody>
</table>

## Test

Esegui i test Python autonomi:

```shell
pytest
pytest tests/test_analyzer.py
pytest tests/test_cli.py
pytest tests/test_gconfiguration_yaml.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

I test coprono la generazione di grafici dell'analizzatore, il comportamento della CLI, la configurazione PyVista tramite YAML
e la generazione dei database di geometria. Per scelta, non richiedono Geant4 o un eseguibile `gemc` compilato; i test
completi di simulazione fanno parte della build Meson del progetto GEMC principale.

## Struttura del progetto

| Percorso                   | Scopo                                                                   |
| ---------------------- | ------------------------------------------------------------------------- |
| `src/pygemc/api/`      | Geometria, materiali, unità, output SQLite, supporto PyVista e modelli |
| `src/pygemc/analyzer/` | Lettori CSV/ROOT, generazione di grafici e CLI dell'analizzatore |
| `tests/`               | Suite pytest autonoma |
| `.github/workflows/`   | Flussi di lavoro per CI, rilascio, pubblicazione su PyPI e integrazione con GEMC |
| `releases/`            | Note di rilascio |
| `pyproject.toml`       | Metadati di distribuzione del pacchetto Python e script da console |
| `meson.build`          | Integrazione come sottoprogetto Meson usata da GEMC |

## Documentazione

- [Guida al flusso di lavoro CI](.github/workflows/README.md)
- [Pagina principale di GEMC](https://gemc.github.io/home/)
- [Panoramica dell'API Python](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [Avvio rapido](https://gemc.github.io/home/documentation/quickstart/)
- [Esempi](https://gemc.github.io/home/examples/)
- [Repository dei sorgenti di GEMC](https://github.com/gemc/src)
- [Repository dei sistemi GEMC per CLAS12](https://github.com/gemc/clas12-systems)
- [Repository del sito di documentazione](https://github.com/gemc/home)
- [Repository GEMC2 / CLAS12](https://github.com/gemc/clas12Tags)

## Contribuire

Mantieni le patch mirate ed esegui i target pytest pertinenti prima di aprire una pull request. Se una modifica interessa la build integrata di GEMC, esegui anche i test Meson del repository principale per gli esempi o i moduli interessati.

## Licenza

`pygemc` è distribuito con la [Licenza Apache, versione 2.0](LICENSE), la stessa licenza usata dal repository principale
dei sorgenti di GEMC. Consulta [`NOTICE`](NOTICE) per i riconoscimenti.

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
