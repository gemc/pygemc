# Dev Release Notes

Install this moving development snapshot directly from GitHub:

```shell
pip install "pygemc @ git+https://github.com/gemc/pygemc.git@dev"
```

## Unreleased changes

- Added PyVista background controls to geometry scripts:
  - `-pvbg`, `--pyvista-background-color` sets the base background color.
  - `-pvbgt`, `--pyvista-background-top` sets the optional top gradient color; use `none` for a flat background.
- Documented light-background VTK.js export usage for documentation images.

<!-- AUTO-DEVMD:START -->
## Commits on main since 2026-05-23

- 2026-05-28 **a466705** - added documents and workflow skips on documents _(by Maurizio Ungaro)_
- 2026-05-28 **820051f** - do not run workflow on README changers and better examples thumbnails _(by Maurizio Ungaro)_
- 2026-05-28 **c986f08** - Update GEMC license coverage to 2026 _(by Maurizio Ungaro)_
- 2026-05-28 **78fddbc** - added proper license _(by Maurizio Ungaro)_
- 2026-05-28 **0ebaa61** - updated README _(by Maurizio Ungaro)_
- 2026-05-27 **f383d62** - rename job _(by Maurizio Ungaro)_
- 2026-05-27 **b2587f4** - renamed ci _(by Maurizio Ungaro)_
- 2026-05-27 **31ad73c** - was triggering wrong workflow _(by Maurizio Ungaro)_
- 2026-05-27 **c90ec9e** - added trigger to deploy and suppress vtk warning in run_geometry _(by Maurizio Ungaro)_
- 2026-05-23 **7036074** - pre-install hatchling in venv to avoid isolated-build PyPI fetch _(by Maurizio Ungaro)_
- 2026-05-23 **e34074c** - relese notes for tagged version _(by Maurizio Ungaro)_
- 2026-05-23 **e837925** - using pygemc venv during installation _(by Maurizio Ungaro)_

<!-- AUTO-DEVMD:END -->
