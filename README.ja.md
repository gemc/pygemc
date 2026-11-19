<!-- TRANSLATIONS:START (managed by bin/translate) -->
**Languages:** [EN](README.md) · [IT](README.it.md) · **日本語** · [FR](README.fr.md) · [中文](README.zh.md)
<!-- TRANSLATIONS:END -->

# pygemc

[![Tests][tests-badge]][tests]
[![Python][python-badge]][pyproject]
[![PyPI][pypi-badge]][pypi]
[![License: Apache-2.0][license-badge]][license]
[![GEMC documentation][docs-badge]][docs]
[![Docker Pulls][dockerhub-badge]][dockerhub]

`pygemc` は、[GEMC](https://github.com/gemc/src) が検出器のジオメトリ、材料、光学特性、ミラー、
および軽量な出力解析ワークフローを定義するために使用する Python API です。Python スクリプトで GEMC データベースを構築し、
PyVista でジオメトリをプレビューし、C++ を書くことなく GEMC の CSV または ROOT 出力を調べることができます。

このパッケージは pip で、または GEMC のソースビルドの一部としてインストールできます。また、
[Docker Hub](https://hub.docker.com/r/gemc/gemc)（および `ghcr.io/gemc/src`）の GEMC Docker イメージにもプリインストールされています。

## 機能

- GEMC のジオメトリおよび材料データベース向けの Python クラス
- ボックス、チューブ、円錐、台形など、一般的な Geant4 ソリッド向けの `GVolume` ヘルパー
- `G4Transform3D` の能動または受動の配置コンストラクタを選択する `GVolume.g4placement_type`
- 化学式、質量分率による混合物、光学特性やシンチレーション特性を扱う `GMaterial` ヘルパー
- `GConfiguration` によるラン、バリエーション、ファクトリ、SQLite、ASCII、PyVista の設定管理
- 検出器スクリプトのセットアップを簡単にする `autogeometry()`
- SQLite および ASCII 形式のデータベース出力
- ジオメトリの確認とドキュメント作成のための PyVista レンダリング、対話型の Qt 表示、VTK.js `.vtksz` エクスポート
- すぐに実行できる検出器システムを生成する `gemc-system-template` CLI
- サポートされている Geant4 ソリッドコンストラクタの Python コードスニペット
- GEMC SQLite データベースファイルを作成・確認する `gemc-sqlite` CLI
- Geant4 のテッセレーションソリッド向けに CAD メッシュ（STL/PLY/OBJ）を簡略化・修復する `gemc-cure-mesh` CLI
- GEMC の CSV または ROOT 出力を要約・プロットする `gemc-analyzer` CLI
- 長さ、角度、時間、エネルギーを表す文字列の単位変換ヘルパー
- コンパイル済みの `gemc` バイナリを必要としない Pytest テストスイート

<br/>

# インストール

pygemc には次の 2 つのインストールモードがあります。用途に応じて選択してください。

- **`latest`** — PyPI で公開されているリリース。デフォルトであり、ほとんどのユーザーに適しています。
- **`dev`** — このソースツリーの編集可能インストール。pygemc 自体の開発やテスト用です。

仮想環境で実行する `pip` コマンドによって、モードを選択します。

```shell
python -m pip install pygemc        # latest: the stable release from PyPI
python -m pip install -e ".[dev]"   # dev: editable checkout, run from the repository root
```

[安定版 PyPI インストール](#stable-pypi-install-latest)と[テスト](#tests)の各セクションで、それぞれの方法を詳しく説明します。

## 安定版 PyPI インストール（`latest`）

`pip` で直接インストールする場合は、仮想環境で Python 3.10〜3.14 を使用してください。バージョンの上限制約は
次のリリースで導入予定です。`pymeshlab` は引き続き必須の依存パッケージです。
Homebrew を使う macOS では、Python 3.14 を明示的にインストールして選択します。

```shell
brew install python@3.14
/opt/homebrew/bin/python3.14 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
python -m pip install --upgrade pip
```

次のコマンドで [PyPI の `pygemc`](https://pypi.org/project/pygemc/) をインストールします。

```shell
python -m pip install pygemc
```
ROOT ファイルの解析に必要なオプションの依存パッケージ:

```shell
python -m pip install "pygemc[root]"
```


## GEMC と一緒にインストールする

次のリリースで追加予定: pygemc が GEMC と CLAS12 システムの Python 環境を管理します。
pygemc の meson サブプロジェクトが Python 3.10〜3.14 を選択し、ビルド環境を作成して、
pygemc とその依存パッケージを `<prefix>/python_env` 以下にインストールするフックを登録します。
GEMC と CLAS12 システムは、どちらもエクスポートされたビルド用インタプリタを使用します。

`<prefix>/bin` と `<prefix>/python_env/bin` を `PATH` に追加すると、GEMC と Python ツールが利用可能になります。

```shell
gemc -v
gemc-system-template --help
gemc-sqlite --help
gemc-analyzer --help
```

<br/>

# クイックスタート

検出器テンプレートを作成します。

```shell
gemc-system-template -s counter
cd counter
./counter.py
```

生成されるシステムには以下が含まれます。

| ファイル       | 用途                                         |
| -------------- | -------------------------------------------- |
| `counter.py`   | メインのジオメトリ構築スクリプト             |
| `geometry.py`  | フラックス検出器を含むボリュームの例         |
| `materials.py` | メタンガス材料の例                           |
| `counter.yaml` | GEMC ステアリングカード                      |
| `README.md`    | 生成された検出器の説明を書き込むための仮のメモ |

PyVista による可視化を有効にして実行します。

```shell
./counter.py -pv
```

VTK.js シーンをエクスポートします。

```shell
./counter.py -pvvtk counter -pvz 0.25
```

ドキュメント用にエクスポートする場合は、明るい単色の背景を使用します。

```shell
./counter.py -pvvtk counter -pvbg "0.92 0.92 0.98" -pvbgt none
```

コンパイル済みの `gemc` 実行ファイルが利用可能な場合は、生成されたシミュレーションを GEMC で実行します。

```shell
gemc counter.yaml
```

出力を解析します。

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --bins 50
```

プロット可能な量は読み込んだファイルの数値列であるため、データを読み込むまで確定せず、
`--help` には表示されません。ファイル名だけを指定して解析ツールを実行すると、取得可能な行数とイベント数、
各ストリームの `plottable <stream>: ...` リストを含む要約が出力されます。
明示的に `--list` オプションを指定しても、同じ要約が出力されます。

```shell
gemc-analyzer counter_t0_digitized.csv
gemc-analyzer counter_t0_digitized.csv --list
```

次のリリースで追加予定: `pid`、`opid`、現在と元の運動量成分を含む真値情報の CSV ファイルでは、
`delta_p`、`delta_theta`、`delta_phi` をプロットできます。これらのプロットには、`pid` が `opid` と一致する行のみが
含まれ、`delta_phi` は区間 [-pi, pi] に折り返されます。`--pid` で特定の粒子種を選択できます。
例: `gemc-analyzer hits_true_info.csv delta_p --pid 11`。

<br/>

# ジオメトリ API

一般的なジオメトリスクリプトでは、設定を作成し、その設定に対してボリュームや材料を登録します。

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

## 配置規約

`GVolume.g4placement_type` は、GEMC がボリュームに使用する Geant4 の配置規約を選択します。

| 値        | 意味                                                                                     |
| --------- | ---------------------------------------------------------------------------------------- |
| `active`  | デフォルト。`G4Transform3D(rotation, translation)` を使用                                |
| `passive` | `G4PVPlacement(rotation, translation, ...)` を使用。GEMC2/clas12Tags の規約に一致        |

新規に作成する GEMC3 ジオメトリの多くは、デフォルトの `active` 規約を使用できます。座標系の回転に依存する、
GEMC2 から移植した検出器システムでは、次のように設定してください。

```python
gvolume.g4placement_type = "passive"
```

このフィールドは SQLite ジオメトリデータベースに書き込まれます。既存の SQLite データベースでは、
ジオメトリスクリプトが新しい行を登録する際に、不足している列が追加されます。

CAD の配置も同じ設定を通じて登録できます（次のリリースで追加予定）。

```python
from pygemc import build_cad

build_cad(cfg, "cad/cad_default.gxml", cad_dir="stls", passive=True)
build_cad(cfg, "stls/cad__default.yaml", passive=True)
```

このヘルパーは GXML、YAML、JSON、または Python の配置マッピングを受け付け、設定の現在の
システム、バリエーション、ラン、出力形式を使用します。既存のバンクは保持されます。メッシュのパスとスケール、`copyOf`
による配置、材料、光学スキン、読み出しフィールドは、`gemc-sqlite -cad` と同じ方法で処理されます。
GEMC2 の座標系の回転には `passive=True` を使用します。`defaults` は共通のボリュームフィールドを指定し、
`material_aliases` はソースの材料名を実行時の名前にマッピングします。検出器固有の配置計算は
引き続き検出器スクリプト内で行い、その結果をマッピングのリストとして渡すことができます。

ジオメトリスクリプトが受け付ける一般的なコマンドラインオプション:

| オプション                   | 用途                                                                           |
|------------------------------|--------------------------------------------------------------------------------|
| `-f`, `--factory`            | `sqlite` または `ascii` 出力を選択                                             |
| `-v`, `--variation`          | ジオメトリのバリエーションを選択                                              |
| `-r`, `--run`                | ラン番号を選択                                                                 |
| `-sql`, `--dbhost`           | SQLite ファイルのパスを選択                                                    |
| `-pv`                        | PyVista ウィンドウを表示                                                       |
| `-pvb`                       | PyVistaQt バックグラウンドプロッターを表示                                     |
| `-pvvtk`                     | VTK.js `.vtksz` シーンをエクスポート                                           |
| `-pvz`                       | VTK.js エクスポートのズームを設定                                              |
| `--pyvista-variation NAME`   | PyVista で 1 つのバリエーションのみを描画。デフォルトは最初に描画されるもの |
| `--pyvista-fast`             | PyVista のボリュームを少数のアクターにまとめ、大規模ジオメトリの描画を高速化 |
| `--no-pyvista-fast`          | PyVista の自動バッチ処理を無効化                                               |
| `--pyvista-fast-threshold N` | 描画されるボリューム数が `N` を超えると PyVista のバッチ処理を自動的に有効化 |
| `-pvbg`                      | PyVista の背景色を名前、16 進数文字列、または `r g b` の 3 成分で設定       |
| `-pvbgt`                     | PyVista の背景グラデーションの上端色を任意に設定。単色の背景には `none` を指定 |
| `--read-yaml`                | GEMC YAML から `g4camera` の方向と `g4view.background` の設定を読み込む      |

## PyVista による可視化

PyVista のサポートは `pygemc` の中心的な機能です。ジオメトリスクリプトでは、検出器を構築しながら表示したり、
対話型の Qt ビューアを開いたり、ドキュメントで公開できる `.vtksz` シーンをエクスポートしたりできます。

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
        材料
      </a>
    </td>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/scintillator_barrel/scintillator_barrel.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/scintillator_barrel/gemc_view.png"
             alt="Scintillator Barrel PyVista" width="180"><br>
        シンチレーターバレル
      </a>
    </td>
  </tr>
</table>

リンクを開くと、GEMC の例から生成された対話型の PyVista シーンを表示できます。

GitHub の README ページには `.vtksz` ファイルを直接埋め込めないため、プレビュー画像から公開済みの VTK.js ビューアにリンクしています。

## コマンドラインツール

<table>
  <thead>
    <tr>
      <th>コマンド</th>
      <th>機能</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -s counter</code></td>
      <td><code>counter</code> という名前の検出器のひな形を生成します。</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -sl</code></td>
      <td>サポートされている Geant4 ソリッドのスニペットを一覧表示します。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -gv G4Box</code></td>
      <td><code>G4Box</code> のボリューム構築スニペットを出力します。</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -gv G4Tubs -write_to geometry.py -geo_sub build_tube</code></td>
      <td><code>G4Tubs</code> のスニペットを <code>geometry.py</code> に書き込みます。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -n mydetector.sqlite</code></td>
      <td>GEMC のジオメトリおよび材料スキーマを持つ新しい SQLite データベースを作成します。</td>
    </tr>
    <tr>
      <td><code>gemc-sqlite -sql mydetector.sqlite -sv</code></td>
      <td>既存のデータベースを開き、そのボリュームを一覧表示します。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -sql mydetector.sqlite -sm</code></td>
      <td>既存のデータベースを開き、その材料を一覧表示します。</td>
    </tr>
    <tr>
      <td>
        <code>gemc-sqlite -sql mydetector.sqlite -sv -ef examples -vf default -sf counter -rf 1</code>
      </td>
      <td>一覧表示するボリュームを、実験、バリエーション、システム、ラン番号で絞り込みます。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-cure-mesh organ.stl -o organ.stl -f 15000</code></td>
      <td>Geant4 向けに CAD メッシュを簡略化・修復します（約 1.5 万面に削減、頂点の結合、穴埋め、面の向きの修正）。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-analyzer counter_t0_digitized.csv</code></td>
      <td>GEMC の CSV 出力ファイルを要約し、ストリームごとにプロット可能な量を一覧表示します。</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer counter_t0_digitized.csv totEdep --bins 50</code></td>
      <td>デジタイズされた変数を 50 ビンでプロットします。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td>
        <code>
          gemc-analyzer counter_t0_true_info.csv --plot yvsx --xlim -20 20 --ylim -20 20
        </code>
      </td>
      <td>真のヒット位置を、横軸 x、縦軸 y の平面にプロットします。</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer out.root E --detector flux --save energy.png</code></td>
      <td>GUI を開かずに、ROOT データを解析した図を保存します。</td>
    </tr>
  </tbody>
</table>

## テスト

パッケージを開発用依存パッケージ（`pytest`、
`pytest-cov`、`ruff`）とともに、編集可能モード（`dev` インストールモード）でインストールします。
これにより、`pytest` は以前にインストールした PyPI の wheel ではなく、ソースツリー内の `src/pygemc` をインポートします。
そうしないと、インストール済みの wheel が優先され、テストの収集に失敗します。

```shell
python -m pip install -e ".[dev]"
```

その後、単独で実行できる Python テストを実行します。

```shell
pytest
pytest tests/test_analyzer.py
pytest tests/test_cli.py
pytest tests/test_gconfiguration_yaml.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

これらのテストは、解析ツールのプロット、CLI の動作、YAML による PyVista 設定、ジオメトリデータベースの生成を
検証します。Geant4 やコンパイル済みの `gemc` 実行ファイルを必要としない設計になっています。完全なシミュレーションテストは、
親プロジェクトである GEMC の meson ビルドに含まれています。

## プロジェクト構成

| パス                   | 用途                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `src/pygemc/api/`      | ジオメトリ、材料、単位、SQLite 出力、PyVista サポート、テンプレート        |
| `src/pygemc/analyzer/` | CSV/ROOT リーダー、プロット、解析 CLI                                      |
| `tests/`               | 単独で実行できる pytest テストスイート                                    |
| `.github/workflows/`   | CI、リリース、PyPI 公開、GEMC 統合の各ワークフロー                         |
| `releases/`            | リリースノート                                                            |
| `pyproject.toml`       | Python パッケージングのメタデータとコンソールスクリプト                    |
| `meson.build`          | GEMC が使用する meson サブプロジェクト統合                                 |

## ドキュメント

- [CI ワークフローガイド](.github/workflows/README.md)
- [GEMC ホームページ](https://gemc.github.io/home/)
- [Python API 概要](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [クイックスタート](https://gemc.github.io/home/documentation/quickstart/)
- [サンプル](https://gemc.github.io/home/examples/)
- [GEMC ソースリポジトリ](https://github.com/gemc/src)
- [CLAS12 GEMC システムのリポジトリ](https://github.com/gemc/clas12-systems)
- [ドキュメントウェブサイトのリポジトリ](https://github.com/gemc/home)
- [GEMC2 / CLAS12 リポジトリ](https://github.com/gemc/clas12Tags)

## コントリビューション

パッチは対象を絞り、プルリクエストを作成する前に関連する pytest ターゲットを実行してください。変更が GEMC との統合ビルドに影響する場合は、影響を受けるサンプルやモジュールについて、親リポジトリの meson テストも実行してください。

## ライセンス

`pygemc` は、メインの GEMC ソースリポジトリと同じ [Apache ライセンス、バージョン 2.0](LICENSE) の下で
提供されています。著作権などの帰属表示については [`NOTICE`](NOTICE) を参照してください。

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
