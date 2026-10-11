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
以及轻量级输出分析工作流。它让用户能够用 Python 脚本构建 GEMC 数据库、用 PyVista 预览几何，
并在无需编写 C++ 的情况下检查 GEMC 的 CSV 或 ROOT 输出。

该软件包可通过 pip 安装，或作为 GEMC 源码构建的一部分安装。它还预装在 GEMC 的
Docker 镜像中，这些镜像可从 [Docker Hub](https://hub.docker.com/r/gemc/gemc)（以及 `ghcr.io/gemc/src`）获取。

## 功能特性

- 用于 GEMC 几何与材料数据库的 Python 类
- `GVolume` 辅助工具，用于构建常见的 Geant4 实体，例如长方体、管、圆锥体和梯形体
- `GVolume.g4placement_type`，用于选择 `G4Transform3D` 的主动或被动变换构造方式
- `GMaterial` 辅助工具，用于化学式、按质量分数配制的混合物，以及光学/闪烁属性
- `GConfiguration`，用于处理运行编号、变体、工厂、SQLite、ASCII 和 PyVista 配置
- `autogeometry()`，为探测器脚本提供便捷的初始化配置
- SQLite 和 ASCII 数据库输出
- PyVista 渲染、交互式 Qt 显示，以及用于几何检查和文档展示的 VTK.js `.vtksz` 导出
- `gemc-system-template` CLI，用于生成可直接运行的探测器系统
- 针对受支持的 Geant4 实体构造函数的 Python 代码片段
- `gemc-sqlite` CLI，用于创建和检查 GEMC SQLite 数据库文件
- `gemc-cure-mesh` CLI，用于为 Geant4 镶嵌实体简化和修复 CAD 网格（STL/PLY/OBJ）
- `gemc-analyzer` CLI，用于汇总和绘制 GEMC 的 CSV 或 ROOT 输出
- 用于长度、角度、时间和能量字符串的单位换算辅助工具
- 无需编译后的 `gemc` 二进制文件即可运行的 Pytest 测试套件

<br/>

# 安装

## 从 PyPI 安装稳定版

直接通过 `pip` 安装时，请使用 Python 虚拟环境。
在使用 Homebrew 的 macOS 上，请使用 `/opt/homebrew/bin/python3` 以确保使用正确的解释器：

```shell
/opt/homebrew/bin/python3 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
python -m pip install --upgrade pip
```

使用以下命令安装 [PyPI 上的 `pygemc`](https://pypi.org/project/pygemc/)：

```shell
python -m pip install pygemc
```
可选的 ROOT 文件分析依赖：

```shell
python -m pip install "pygemc[root]"
```


## 随 GEMC 一起安装

从源码构建 GEMC 后，无需任何激活步骤或单独通过 pip 安装，即可在脚本中使用 pygemc，
同时也可使用 gemc 和 Python 工具：

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

| 文件           | 用途                                         |
| -------------- | -------------------------------------------- |
| `counter.py`   | 主几何构建脚本                               |
| `geometry.py`  | 示例几何体，包括一个通量探测器               |
| `materials.py` | 示例甲烷气体材料                             |
| `counter.yaml` | GEMC 控制卡                                  |
| `README.md`    | 为生成的探测器预留的占位说明                 |

运行并使用 PyVista 可视化：

```shell
./counter.py -pv
```

导出一个 VTK.js 场景：

```shell
./counter.py -pvvtk counter -pvz 0.25
```

为文档导出使用浅色纯色背景：

```shell
./counter.py -pvvtk counter -pvbg "0.92 0.92 0.98" -pvbgt none
```

当编译后的 `gemc` 可执行文件可用时，用 GEMC 运行生成的仿真：

```shell
gemc counter.yaml
```

分析输出：

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --bins 50
```

可供绘制的量是所加载文件中的数值列，因此只有在读取数据后才能确定，
不会出现在 `--help` 中。仅提供文件名运行分析器即可打印摘要，
其中包含可获取的行数和事件数，以及每个数据流的 `plottable <stream>: ...` 列表。
显式指定 `--list` 选项会打印相同的摘要：

```shell
gemc-analyzer counter_t0_digitized.csv
gemc-analyzer counter_t0_digitized.csv --list
```

下一版本即将推出：包含 `pid`、`opid` 以及当前与原始动量分量的真值信息 CSV 文件将提供
`delta_p`、`delta_theta` 和 `delta_phi`。只有 `pid` 与 `opid` 相同的行才会参与这些图的绘制；
`delta_phi` 会按周期映射到区间 [-pi, pi]。使用 `--pid` 选择一种粒子，
例如 `gemc-analyzer hits_true_info.csv delta_p --pid 11`。

<br/>

# 几何 API

典型的几何脚本会创建一个配置，并将几何体/材料发布到该配置中：

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

`GVolume.g4placement_type` 用于选择 GEMC 为某个几何体使用的 Geant4 放置约定：

| 值        | 含义                                                                                     |
| --------- | ---------------------------------------------------------------------------------------- |
| `active`  | 默认值；使用 `G4Transform3D(rotation, translation)`                                       |
| `passive` | 使用 `G4PVPlacement(rotation, translation, ...)`，与 GEMC2/clas12Tags 约定一致             |

大多数新的 GEMC3 几何可以使用默认的 `active` 约定。从 GEMC2 移植、
且依赖坐标系旋转的探测器系统应设置为：

```python
gvolume.g4placement_type = "passive"
```

该字段会写入 SQLite 几何数据库。当几何脚本发布新行时，
现有的 SQLite 数据库会自动升级，补上缺失的列。

几何脚本接受的常用命令行选项：

| 选项                         | 用途                                                                           |
|------------------------------|--------------------------------------------------------------------------------|
| `-f`, `--factory`            | 选择 `sqlite` 或 `ascii` 输出                                                   |
| `-v`, `--variation`          | 选择几何变体                                                                   |
| `-r`, `--run`                | 选择运行编号                                                                   |
| `-sql`, `--dbhost`           | 选择 SQLite 文件路径                                                           |
| `-pv`                        | 显示一个 PyVista 窗口                                                          |
| `-pvb`                       | 显示一个 PyVistaQt 后台绘图器                                                  |
| `-pvvtk`                     | 导出一个 VTK.js `.vtksz` 场景                                                  |
| `-pvz`                       | 设置 VTK.js 导出的缩放比例                                                     |
| `--pyvista-variation NAME`   | 在 PyVista 中仅渲染一个变体；默认选择已渲染变体中的第一个                        |
| `--pyvista-fast`             | 将 PyVista 几何体批量合并为更少的 actor，以加快大型几何的渲染                    |
| `--no-pyvista-fast`          | 禁用自动的 PyVista 批量合并                                                     |
| `--pyvista-fast-threshold N` | 当渲染的几何体数量超过 `N` 时自动启用 PyVista 批量合并                           |
| `-pvbg`                      | 通过颜色名称、十六进制字符串或 `r g b` 三元组设置 PyVista 背景色                |
| `-pvbgt`                     | 设置可选的 PyVista 顶部渐变色；使用 `none` 设置纯色背景                         |
| `--read-yaml`                | 从 GEMC YAML 中读取 `g4camera` 方向和 `g4view.background` 设置                  |

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

GitHub README 页面无法直接嵌入 `.vtksz` 文件，因此预览图片链接到托管的 VTK.js 查看器。

## 命令行工具

<table>
  <thead>
    <tr>
      <th>命令</th>
      <th>功能</th>
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
      <td>将一个 <code>G4Tubs</code> 代码片段写入 <code>geometry.py</code>。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -n mydetector.sqlite</code></td>
      <td>创建一个采用 GEMC 几何与材料数据库模式的新 SQLite 数据库。</td>
    </tr>
    <tr>
      <td><code>gemc-sqlite -sql mydetector.sqlite -sv</code></td>
      <td>打开一个现有数据库并列出其几何体。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -sql mydetector.sqlite -sm</code></td>
      <td>打开一个现有数据库并列出其材料。</td>
    </tr>
    <tr>
      <td>
        <code>gemc-sqlite -sql mydetector.sqlite -sv -ef examples -vf default -sf counter -rf 1</code>
      </td>
      <td>按实验、变体、系统和运行编号筛选所列出的几何体。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-cure-mesh organ.stl -o organ.stl -f 15000</code></td>
      <td>为 Geant4 简化和修复 CAD 网格（减面至约 1.5 万个面片、合并重合顶点、补洞、调整面片方向）。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-analyzer counter_t0_digitized.csv</code></td>
      <td>汇总一个 GEMC CSV 输出文件，并列出每个数据流中可绘制的量。</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer counter_t0_digitized.csv totEdep --bins 50</code></td>
      <td>使用 50 个分箱绘制一个数字化变量。</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td>
        <code>
          gemc-analyzer counter_t0_true_info.csv --plot yvsx --xlim -20 20 --ylim -20 20
        </code>
      </td>
      <td>以 x 为横轴、y 为纵轴绘制击中位置的真值。</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer out.root E --detector flux --save energy.png</code></td>
      <td>保存分析器根据 ROOT 数据生成的图像，无需打开 GUI。</td>
    </tr>
  </tbody>
</table>

## 测试

运行独立的 Python 测试：

```shell
pytest
pytest tests/test_analyzer.py
pytest tests/test_cli.py
pytest tests/test_gconfiguration_yaml.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

这些测试涵盖分析器绘图、CLI 行为、由 YAML 驱动的 PyVista 配置，以及几何数据库
生成。测试特意设计为无需 Geant4 或编译后的 `gemc` 可执行文件；完整的仿真测试
位于上层 GEMC 的 Meson 构建中。

## 项目结构

| 路径                   | 用途                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `src/pygemc/api/`      | 几何、材料、单位、SQLite 输出、PyVista 支持和模板                          |
| `src/pygemc/analyzer/` | CSV/ROOT 读取器、绘图和分析器 CLI                                          |
| `tests/`               | 独立的 pytest 测试套件                                                     |
| `.github/workflows/`   | CI、发布、PyPI 发布和 GEMC 集成工作流                                      |
| `releases/`            | 发布说明                                                                  |
| `pyproject.toml`       | Python 打包元数据和控制台脚本                                              |
| `meson.build`          | GEMC 使用的 Meson 子项目集成                                               |

## 文档

- [CI 工作流指南](.github/workflows/README.md)
- [GEMC 主页](https://gemc.github.io/home/)
- [Python API 概览](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [快速上手](https://gemc.github.io/home/documentation/quickstart/)
- [示例](https://gemc.github.io/home/examples/)
- [GEMC 源码仓库](https://github.com/gemc/src)
- [CLAS12 GEMC 系统仓库](https://github.com/gemc/clas12-systems)
- [文档网站仓库](https://github.com/gemc/home)
- [GEMC2 / CLAS12 仓库](https://github.com/gemc/clas12Tags)

## 贡献

请保持补丁聚焦，并在提交拉取请求之前运行相关的 pytest 测试目标。如果更改影响集成的 GEMC 构建，
还应针对受影响的示例或模块运行上层仓库的 Meson 测试。

## 许可证

`pygemc` 采用 [Apache 许可证 2.0 版](LICENSE)，与主 GEMC 源码仓库
使用相同的许可证。有关署名信息，请参见 [`NOTICE`](NOTICE)。

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
