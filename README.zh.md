<!-- TRANSLATIONS:START (managed by bin/translate) -->
**Languages:** [EN](README.md) · [IT](README.it.md) · [日本語](README.ja.md) · [FR](README.fr.md) · **中文**
<!-- TRANSLATIONS:END -->

# pygemc

[![测试][tests-badge]][tests]
[![Python][python-badge]][pyproject]
[![PyPI][pypi-badge]][pypi]
[![许可证：Apache-2.0][license-badge]][license]
[![GEMC 文档][docs-badge]][docs]
[![Docker 拉取次数][dockerhub-badge]][dockerhub]

`pygemc` 是 [GEMC](https://github.com/gemc/src) 使用的 Python API，用于定义探测器几何、材料、光学属性、反射镜，
以及轻量级的输出分析工作流。用户可以通过 Python 脚本构建 GEMC 数据库，用 PyVista 预览几何，
并在无需编写 C++ 的情况下查看 GEMC 的 CSV 或 ROOT 输出。

该软件包可通过 pip 安装，也可作为 GEMC 源码构建的一部分安装。它还预装在
[Docker Hub](https://hub.docker.com/r/gemc/gemc) 上的 GEMC Docker 镜像中（以及 `ghcr.io/gemc/src`）。

## 功能特性

- 用于 GEMC 几何与材料数据库的 Python 类
- `GVolume` 辅助工具，支持盒体、管体、锥体和梯形体等常见 Geant4 实体
- `GVolume.g4placement_type`，用于选择 `G4Transform3D` 的主动或被动变换构造函数
- `GMaterial` 辅助工具，支持化学式、按质量分数组成的混合物以及光学/闪烁属性
- `GConfiguration`，用于处理运行编号、变体、工厂、SQLite、ASCII 和 PyVista 配置
- `autogeometry()`，为探测器脚本提供便捷的初始化设置
- SQLite 和 ASCII 数据库输出
- PyVista 渲染、交互式 Qt 显示，以及用于几何检查和文档展示的 VTK.js `.vtksz` 导出
- `gemc-system-template` 命令行工具，用于生成可直接运行的探测器系统
- 适用于受支持 Geant4 实体构造函数的 Python 代码片段
- `gemc-sqlite` 命令行工具，用于创建和检查 GEMC SQLite 数据库文件
- `gemc-cure-mesh` 命令行工具，用于为 Geant4 镶嵌实体简化和修复 CAD 网格（STL/PLY/OBJ）
- `gemc-analyzer` 命令行工具，用于汇总和绘制 GEMC 的 CSV 或 ROOT 输出
- 用于长度、角度、时间和能量字符串的单位换算辅助工具
- 无需已编译的 `gemc` 二进制文件即可运行的 Pytest 测试套件

<br/>

# 安装

pygemc 有两种安装模式；请根据需要选择：

- **`latest`** — PyPI 上发布的正式版本。这是默认模式，适合大多数用户。
- **`dev`** — 以可编辑方式安装当前源码树，用于开发或测试 pygemc 本身。

在虚拟环境中选择相应的 `pip` 命令，即可确定安装模式：

```shell
python -m pip install pygemc        # latest: the stable release from PyPI
python -m pip install -e ".[dev]"   # dev: editable checkout, run from the repository root
```

[通过 PyPI 安装稳定版](#stable-pypi-install-latest) 和 [测试](#tests) 两节分别详细介绍了这两种方式。

## 通过 PyPI 安装稳定版 (`latest`)

直接使用 `pip` 安装时，请在虚拟环境中使用 Python 3.10-3.14。该版本上限将于下一版本引入；
`pymeshlab` 仍是必需依赖。
在使用 Homebrew 的 macOS 上，请显式安装并选择 Python 3.14：

```shell
brew install python@3.14
/opt/homebrew/bin/python3.14 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
python -m pip install --upgrade pip
```

通过以下命令[从 PyPI 安装 `pygemc`](https://pypi.org/project/pygemc/)：

```shell
python -m pip install pygemc
```
可选的 ROOT 文件分析依赖：

```shell
python -m pip install "pygemc[root]"
```


## 随 GEMC 一同安装

即将在下一版本推出：pygemc 管理 GEMC 和 CLAS12 系统的 Python 环境。
其 Meson 子项目会选择 Python 3.10-3.14，创建构建环境，并注册安装钩子，
将 pygemc 及其依赖安装到 `<prefix>/python_env` 下。
两个使用方都使用该子项目导出的构建用 Python 解释器。

将 `<prefix>/bin` 和 `<prefix>/python_env/bin` 添加到 `PATH` 后，即可使用 GEMC 和这些 Python 工具：

```shell
gemc -v
gemc-system-template --help
gemc-sqlite --help
gemc-analyzer --help
```

<br/>

# 快速上手

创建一个探测器模板：

```shell
gemc-system-template -s counter
cd counter
./counter.py
```

生成的系统包含：

| 文件           | 用途                                      |
| -------------- | -------------------------------------------- |
| `counter.py`   | 主几何构建脚本                 |
| `geometry.py`  | 示例几何体，包括一个通量探测器   |
| `materials.py` | 示例甲烷气体材料                 |
| `counter.yaml` | GEMC 控制卡                           |
| `README.md`    | 为生成的探测器预留的说明 |

启用 PyVista 可视化运行：

```shell
./counter.py -pv
```

导出 VTK.js 场景：

```shell
./counter.py -pvvtk counter -pvz 0.25
```

导出用于文档展示的场景时，使用浅色纯色背景：

```shell
./counter.py -pvvtk counter -pvbg "0.92 0.92 0.98" -pvbgt none
```

在已编译的 `gemc` 可执行文件可用时，用 GEMC 运行生成的模拟：

```shell
gemc counter.yaml
```

分析输出：

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --bins 50
```

可供绘图的量对应于所加载文件中的数值列，因此只有在读取数据后才能确定，
不会出现在 `--help` 中。仅指定文件名运行分析器即可打印摘要，其中包括可获取的行数和事件数，
以及每个数据流的 `plottable <stream>: ...` 列表。显式指定 `--list` 选项也会打印相同的摘要：

```shell
gemc-analyzer counter_t0_digitized.csv
gemc-analyzer counter_t0_digitized.csv --list
```

即将在下一版本推出：包含 `pid`、`opid` 以及当前和原始动量分量的真值信息 CSV 文件
将提供 `delta_p`、`delta_theta` 和 `delta_phi`。只有 `pid` 与 `opid` 相同的行才会纳入
这些图；`delta_phi` 会按周期归一化到区间 [-pi, pi]。使用 `--pid` 选择一种粒子，
例如 `gemc-analyzer hits_true_info.csv delta_p --pid 11`。

<br/>

# 几何 API

典型的几何脚本会创建一个配置，并向其发布几何体和材料：

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

## 放置约定

`GVolume.g4placement_type` 用于选择 GEMC 对某个几何体采用的 Geant4 放置约定：

| 取值     | 含义                                                                                  |
| --------- | ---------------------------------------------------------------------------------------- |
| `active`  | 默认值；使用 `G4Transform3D(rotation, translation)`                                     |
| `passive` | 使用 `G4PVPlacement(rotation, translation, ...)`，与 GEMC2/clas12Tags 的约定一致 |

大多数新的 GEMC3 几何可以使用默认的 `active` 约定。从 GEMC2 移植且依赖
坐标系旋转的探测器系统应设置：

```python
gvolume.g4placement_type = "passive"
```

该字段会写入 SQLite 几何数据库。当几何脚本发布新行时，现有 SQLite 数据库
会自动补上缺失的列。

CAD 放置也可以通过同一配置发布（即将在下一版本推出）：

```python
from pygemc import build_cad

build_cad(cfg, "cad/cad_default.gxml", cad_dir="stls", passive=True)
build_cad(cfg, "stls/cad__default.yaml", passive=True)
```

该辅助函数接受 GXML、YAML、JSON 或 Python 放置映射，并使用配置当前的
系统、变体、运行编号和输出格式。它会保留现有的数据组（bank）。网格路径和缩放、`copyOf`
放置、材料、光学包覆表面和读出字段的处理方式与 `gemc-sqlite -cad` 相同。
对于 GEMC2 的坐标系旋转，请使用 `passive=True`。`defaults` 提供共享的几何体字段，
`material_aliases` 将源材料名称映射到运行时名称。探测器特有的放置计算
仍保留在探测器脚本中，其结果可以映射列表的形式传入。

几何脚本接受的常见命令行选项：

| 选项                       | 用途                                                                        |
|------------------------------|--------------------------------------------------------------------------------|
| `-f`, `--factory`            | 选择 `sqlite` 或 `ascii` 输出                                              |
| `-v`, `--variation`          | 选择几何变体                                                  |
| `-r`, `--run`                | 选择运行编号                                                          |
| `-sql`, `--dbhost`           | 选择 SQLite 文件路径                                                    |
| `-pv`                        | 显示 PyVista 窗口                                                          |
| `-pvb`                       | 显示 PyVistaQt 后台绘图器                                            |
| `-pvvtk`                     | 导出 VTK.js `.vtksz` 场景                                                 |
| `-pvz`                       | 设置 VTK.js 导出的缩放比例                                                     |
| `--pyvista-variation NAME`   | 在 PyVista 中仅渲染一个变体；默认为第一个被渲染的变体 |
| `--pyvista-fast`             | 将 PyVista 几何体批量合并为更少的渲染对象，以加快大型几何的渲染    |
| `--no-pyvista-fast`          | 禁用 PyVista 自动批处理                                             |
| `--pyvista-fast-threshold N` | 渲染的几何体数量超过 `N` 时自动启用 PyVista 批处理                        |
| `-pvbg`                      | 通过颜色名称、十六进制字符串或 `r g b` 三元组设置 PyVista 背景色      |
| `-pvbgt`                     | 设置可选的 PyVista 顶部渐变色；使用 `none` 设置纯色背景  |
| `--read-yaml`                | 从 GEMC YAML 读取 `g4camera` 方向和 `g4view.background` 设置    |

## PyVista 可视化

PyVista 支持是 `pygemc` 的核心功能：几何脚本可以在构建探测器的同时显示它，
打开交互式 Qt 查看器，或导出可在文档中发布的 `.vtksz` 场景。

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
        桶形闪烁体
      </a>
    </td>
  </tr>
</table>

点击链接，打开由 GEMC 示例生成的交互式 PyVista 场景。

GitHub README 页面无法直接嵌入 `.vtksz` 文件，因此预览图链接到托管的 VTK.js 查看器。

## 命令行工具

<table>
  <thead>
    <tr>
      <th>命令</th>
      <th>作用</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -s counter</code></td>
      <td>生成一个名为 <code>counter</code> 的探测器骨架。</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -sl</code></td>
      <td>列出受支持的 Geant4 实体代码片段。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -gv G4Box</code></td>
      <td>打印用于构建 <code>G4Box</code> 几何体的代码片段。</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -gv G4Tubs -write_to geometry.py -geo_sub build_tube</code></td>
      <td>将 <code>G4Tubs</code> 代码片段写入 <code>geometry.py</code>。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -n mydetector.sqlite</code></td>
      <td>创建具有 GEMC 几何与材料数据库模式的新 SQLite 数据库。</td>
    </tr>
    <tr>
      <td><code>gemc-sqlite -sql mydetector.sqlite -sv</code></td>
      <td>打开现有数据库并列出其中的几何体。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -sql mydetector.sqlite -sm</code></td>
      <td>打开现有数据库并列出其中的材料。</td>
    </tr>
    <tr>
      <td>
        <code>gemc-sqlite -sql mydetector.sqlite -sv -ef examples -vf default -sf counter -rf 1</code>
      </td>
      <td>按实验、变体、系统和运行编号筛选列出的几何体。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-cure-mesh organ.stl -o organ.stl -f 15000</code></td>
      <td>为 Geant4 简化和修复 CAD 网格（减至约 1.5 万个面、合并顶点、填补孔洞、调整面朝向）。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-analyzer counter_t0_digitized.csv</code></td>
      <td>汇总 GEMC CSV 输出文件，并列出每个数据流中可供绘图的量。</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer counter_t0_digitized.csv totEdep --bins 50</code></td>
      <td>使用 50 个分箱绘制数字化变量。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td>
        <code>
          gemc-analyzer counter_t0_true_info.csv --plot yvsx --xlim -20 20 --ylim -20 20
        </code>
      </td>
      <td>在 y 对 x 的平面上绘制真实击中位置。</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer out.root E --detector flux --save energy.png</code></td>
      <td>保存基于 ROOT 数据的分析器图像，无需打开图形界面。</td>
    </tr>
  </tbody>
</table>

## 测试

以可编辑模式（`dev` 安装模式）安装该软件包及其开发依赖（`pytest`、
`pytest-cov`、`ruff`）。可编辑安装还会使 `pytest` 导入源码树内的 `src/pygemc` 源码，
避免此前安装的 PyPI wheel 包遮蔽这些源码，导致测试收集失败：

```shell
python -m pip install -e ".[dev]"
```

然后运行独立的 Python 测试：

```shell
pytest
pytest tests/test_analyzer.py
pytest tests/test_cli.py
pytest tests/test_gconfiguration_yaml.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

这些测试覆盖分析器绘图、命令行行为、由 YAML 驱动的 PyVista 配置，以及几何数据库
生成。它们在设计上无需 Geant4 或已编译的 `gemc` 可执行文件；完整的模拟测试
位于上层 GEMC 的 Meson 构建中。

## 项目结构

| 路径                   | 用途                                                                   |
| ---------------------- | ------------------------------------------------------------------------- |
| `src/pygemc/api/`      | 几何、材料、单位、SQLite 输出、PyVista 支持和模板 |
| `src/pygemc/analyzer/` | CSV/ROOT 读取器、绘图和分析器命令行工具                              |
| `tests/`               | 独立的 pytest 测试套件                                                   |
| `.github/workflows/`   | CI、版本发布、PyPI 发布和 GEMC 集成工作流            |
| `releases/`            | 发布说明                                                             |
| `pyproject.toml`       | Python 打包元数据和控制台脚本                             |
| `meson.build`          | GEMC 使用的 Meson 子项目集成                                 |

## 文档

- [CI 工作流指南](.github/workflows/README.md)
- [GEMC 主页](https://gemc.github.io/home/)
- [Python API 概述](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [快速上手](https://gemc.github.io/home/documentation/quickstart/)
- [示例](https://gemc.github.io/home/examples/)
- [GEMC 源码仓库](https://github.com/gemc/src)
- [CLAS12 GEMC 系统仓库](https://github.com/gemc/clas12-systems)
- [文档网站仓库](https://github.com/gemc/home)
- [GEMC2 / CLAS12 仓库](https://github.com/gemc/clas12Tags)

## 参与贡献

请保持补丁聚焦，并在发起拉取请求前运行相关的 pytest 测试目标。如果更改影响集成的 GEMC 构建，还应针对受影响的示例或模块运行上层仓库的 Meson 测试。

## 许可证

`pygemc` 采用 [Apache 许可证 2.0 版](LICENSE)，与 GEMC 主源码仓库
使用相同的许可证。有关署名信息，请参见 [`NOTICE`](NOTICE)。

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
