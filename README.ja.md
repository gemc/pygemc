<!-- TRANSLATIONS:START (managed by bin/translate) -->
**Languages:** [EN](README.md) · [IT](README.it.md) · **日本語** · [FR](README.fr.md) · [中文](README.zh.md)
<!-- TRANSLATIONS:END -->

# pygemc

[![テスト][tests-badge]][tests]
[![Python][python-badge]][pyproject]
[![PyPI][pypi-badge]][pypi]
[![ライセンス: Apache-2.0][license-badge]][license]
[![GEMC ドキュメント][docs-badge]][docs]
[![Docker プル数][dockerhub-badge]][dockerhub]

`pygemc` は、検出器のジオメトリ、材料、光学特性、ミラー、および軽量な出力解析ワークフローを定義するために
[GEMC](https://github.com/gemc/src) が使用する Python API です。ユーザーは Python スクリプトで GEMC データベースを
構築し、PyVista でジオメトリをプレビューし、C++ を書くことなく GEMC の CSV または ROOT 出力を調べられます。

このパッケージは pip で、または GEMC のソースビルドの一部としてインストールできます。また、
[Docker Hub](https://hub.docker.com/r/gemc/gemc)（および `ghcr.io/gemc/src`）で提供される GEMC Docker イメージに
プリインストールされています。

## 機能

- GEMC ジオメトリおよび材料データベース用の Python クラス
- 直方体、円筒、円錐、台形などの一般的な Geant4 ソリッド向けの `GVolume` ヘルパー
- `G4Transform3D` の能動変換または受動変換のコンストラクタを選択する `GVolume.g4placement_type`
- 化学式、質量分率による混合物、および光学／シンチレーション特性のための `GMaterial` ヘルパー
- `GConfiguration` によるラン、バリエーション、ファクトリ、SQLite、ASCII、PyVista の設定管理
- 検出器スクリプトのセットアップを簡単にする `autogeometry()`
- SQLite および ASCII データベース出力
- ジオメトリの確認とドキュメント作成のための PyVista レンダリング、対話型 Qt 表示、VTK.js `.vtksz` エクスポート
- すぐに実行できる検出器システムを生成する `gemc-system-template` CLI
- サポートされている Geant4 ソリッドコンストラクタ用の Python コードスニペット
- GEMC SQLite データベースファイルを作成・検査する `gemc-sqlite` CLI
- Geant4 のテッセレーションソリッド用に CAD メッシュ（STL/PLY/OBJ）を簡略化・修復する `gemc-cure-mesh` CLI
- GEMC の CSV または ROOT 出力を要約・プロットする `gemc-analyzer` CLI
- 長さ、角度、時間、エネルギーを表す文字列の単位変換ヘルパー
- コンパイル済みの `gemc` バイナリを必要としない Pytest スイート

<br/>

# インストール

## PyPI からの安定版インストール

`pip` で直接インストールする場合は Python 仮想環境を使用してください。
Homebrew を使う macOS では、正しいインタプリタが使われるように `/opt/homebrew/bin/python3` を使用します:

```shell
/opt/homebrew/bin/python3 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
python -m pip install --upgrade pip
```

[PyPI の `pygemc`](https://pypi.org/project/pygemc/) を次のコマンドでインストールします:

```shell
python -m pip install pygemc
```
ROOT ファイル解析用の追加依存パッケージ（任意）:

```shell
python -m pip install "pygemc[root]"
```


## GEMC と一緒にインストール

GEMC をソースからビルドすると、アクティベーション手順や個別の pip インストールなしでスクリプトから pygemc を
利用でき、gemc と Python ツールも使えるようになります:

```shell
gemc -v
gemc-system-template --help
gemc-sqlite --help
gemc-analyzer --help
```

<br/>

# クイックスタート

検出器テンプレートを作成します:

```shell
gemc-system-template -s counter
cd counter
./counter.py
```

生成されるシステムには次が含まれます:

| ファイル       | 用途                                         |
| -------------- | -------------------------------------------- |
| `counter.py`   | メインのジオメトリ構築スクリプト               |
| `geometry.py`  | フラックス検出器を含むボリュームの例           |
| `materials.py` | メタンガス材料の例                            |
| `counter.yaml` | GEMC ステアリングカード                       |
| `README.md`    | 生成された検出器の説明を書き込むためのひな形   |

PyVista による可視化付きで実行します:

```shell
./counter.py -pv
```

VTK.js シーンをエクスポートします:

```shell
./counter.py -pvvtk counter -pvz 0.25
```

ドキュメント用のエクスポートには明るい単色の背景を使用します:

```shell
./counter.py -pvvtk counter -pvbg "0.92 0.92 0.98" -pvbgt none
```

コンパイル済みの `gemc` 実行ファイルが利用可能な場合、生成されたシミュレーションを GEMC で実行します:

```shell
gemc counter.yaml
```

出力を解析します:

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --bins 50
```

プロット可能な量は読み込んだファイルの数値列であり、データを読み込んではじめて判明するため、
`--help` には表示されません。ファイル名だけを指定してアナライザを実行すると、行数・イベント数（取得可能な場合）を
含む要約と、各ストリームの `plottable <stream>: ...` 一覧が出力されます。
明示的な `--list` オプションでも同じ要約が出力されます:

```shell
gemc-analyzer counter_t0_digitized.csv
gemc-analyzer counter_t0_digitized.csv --list
```

次のリリースで提供予定: `pid`、`opid`、および現在と元の運動量成分を含む真値情報 CSV ファイルでは、
`delta_p`、`delta_theta`、`delta_phi` が利用できるようになります。`pid` が `opid` と一致する行のみがこれらの
プロットの対象となり、`delta_phi` は区間 [-pi, pi] に収まるよう周期的に折り返されます。`--pid` で粒子種を 1 つ選択します。
例: `gemc-analyzer hits_true_info.csv delta_p --pid 11`。

<br/>

# ジオメトリ API

一般的なジオメトリスクリプトでは、設定を作成し、その設定にボリュームや材料を登録します:

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

## 配置の規約

`GVolume.g4placement_type` は、GEMC がボリュームに使用する Geant4 の配置規約を選択します:

| 値        | 意味                                                                                     |
| --------- | ---------------------------------------------------------------------------------------- |
| `active`  | デフォルト。`G4Transform3D(rotation, translation)` を使用                                 |
| `passive` | `G4PVPlacement(rotation, translation, ...)` を使用し、GEMC2/clas12Tags の規約に一致       |

新しい GEMC3 ジオメトリのほとんどは、デフォルトの `active` 規約を使用できます。GEMC2 から移植された検出器システムで
座標系の回転に依存する場合は、次のように設定してください:

```python
gvolume.g4placement_type = "passive"
```

このフィールドは SQLite ジオメトリデータベースに書き込まれます。既存の SQLite データベースには、ジオメトリ
スクリプトが新しい行を登録する際に不足している列が追加され、更新されます。

ジオメトリスクリプトが受け付ける一般的なコマンドラインオプション:

| オプション                   | 用途                                                                           |
|------------------------------|--------------------------------------------------------------------------------|
| `-f`, `--factory`            | `sqlite` または `ascii` の出力を選択                                           |
| `-v`, `--variation`          | ジオメトリのバリエーションを選択                                               |
| `-r`, `--run`                | ラン番号を選択                                                                 |
| `-sql`, `--dbhost`           | SQLite ファイルのパスを選択                                                    |
| `-pv`                        | PyVista ウィンドウを表示                                                       |
| `-pvb`                       | PyVistaQt のバックグラウンドプロッターを表示                                    |
| `-pvvtk`                     | VTK.js `.vtksz` シーンをエクスポート                                           |
| `-pvz`                       | VTK.js エクスポートのズームを設定                                              |
| `--pyvista-variation NAME`   | PyVista で 1 つのバリエーションのみを描画。既定は最初に描画されるバリエーション |
| `--pyvista-fast`             | 大規模ジオメトリの描画を高速化するため PyVista ボリュームを少数のアクターにまとめる |
| `--no-pyvista-fast`          | PyVista の自動バッチ処理を無効化                                               |
| `--pyvista-fast-threshold N` | 描画されるボリューム数が `N` を超えると PyVista のバッチ処理を自動で有効化       |
| `-pvbg`                      | PyVista の背景色を名前、16 進文字列、または `r g b` の 3 値で設定               |
| `-pvbgt`                     | PyVista の背景グラデーションの上部の色を任意で設定。単色の背景には `none` を使用 |
| `--read-yaml`                | GEMC YAML から `g4camera` の方向と `g4view.background` の設定を読み込む         |

## PyVista による可視化

PyVista サポートは `pygemc` の中核をなす機能です。ジオメトリスクリプトで検出器を構築しながら表示したり、
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

リンクを開くと、GEMC のサンプルから生成された対話型の PyVista シーンを表示できます。

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
      <td>一覧表示するボリュームを実験、バリエーション、システム、ラン番号で絞り込みます。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-cure-mesh organ.stl -o organ.stl -f 15000</code></td>
      <td>Geant4 用に CAD メッシュを簡略化・修復します（約 1 万 5 千面への削減、頂点の結合、穴埋め、面の向きの修正）。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-analyzer counter_t0_digitized.csv</code></td>
      <td>GEMC の CSV 出力ファイルを要約し、ストリームごとにプロット可能な量を一覧表示します。</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer counter_t0_digitized.csv totEdep --bins 50</code></td>
      <td>デジタイズ後の変数を 50 ビンでプロットします。</td>
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
      <td>GUI を開かずに、ROOT データに基づくアナライザの図を保存します。</td>
    </tr>
  </tbody>
</table>

## テスト

スタンドアロンの Python テストを実行します:

```shell
pytest
pytest tests/test_analyzer.py
pytest tests/test_cli.py
pytest tests/test_gconfiguration_yaml.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

これらのテストは、アナライザのプロット、CLI の動作、YAML に基づく PyVista 設定、ジオメトリデータベースの
生成を検証します。Geant4 やコンパイル済みの `gemc` 実行ファイルを必要としないように設計されています。
完全なシミュレーションテストは、親 GEMC の Meson ビルドに含まれています。

## プロジェクト構成

| パス                   | 用途                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `src/pygemc/api/`      | ジオメトリ、材料、単位、SQLite 出力、PyVista サポート、およびテンプレート    |
| `src/pygemc/analyzer/` | CSV/ROOT リーダー、プロット、およびアナライザ CLI                           |
| `tests/`               | スタンドアロンの pytest スイート                                           |
| `.github/workflows/`   | CI、リリース、PyPI 公開、および GEMC 統合ワークフロー                       |
| `releases/`            | リリースノート                                                            |
| `pyproject.toml`       | Python パッケージングのメタデータとコンソールスクリプト                     |
| `meson.build`          | GEMC が使用する Meson サブプロジェクト統合                                 |

## ドキュメント

- [CI ワークフローガイド](.github/workflows/README.md)
- [GEMC ホームページ](https://gemc.github.io/home/)
- [Python API 概要](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [クイックスタート](https://gemc.github.io/home/documentation/quickstart/)
- [サンプル](https://gemc.github.io/home/examples/)
- [GEMC ソースリポジトリ](https://github.com/gemc/src)
- [CLAS12 GEMC システムリポジトリ](https://github.com/gemc/clas12-systems)
- [ドキュメントウェブサイトリポジトリ](https://github.com/gemc/home)
- [GEMC2 / CLAS12 リポジトリ](https://github.com/gemc/clas12Tags)

## コントリビューション

パッチは変更の範囲を絞り、プルリクエストを作成する前に関連する pytest ターゲットを実行してください。変更が GEMC の統合ビルドに影響する場合は、影響を受けるサンプルやモジュールについて、親リポジトリの Meson テストも実行してください。

## ライセンス

`pygemc` は、メインの GEMC ソースリポジトリと同じ [Apache License, Version 2.0](LICENSE) の下で
提供されています。著作権者などの帰属情報については [`NOTICE`](NOTICE) を参照してください。

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
