# GitHub Actions workflows

This directory contains the test, release, package-publication, and GEMC integration workflows for pygemc. The
[GEMC workflow guide][src-workflows] is the authoritative description of the complete
`pygemc -> src -> clas12-systems` dependency chain.

## Integration path

A pygemc push to `main` starts two independent workflows:

```text
pygemc push to main
  |-> pygemc tests
  `-> Trigger GEMC compatibility test
      -> src Test after pygemc
      -> src Deploy
      -> src Binary Tarballs
      -> clas12-systems compatibility Test and Deploy
```

The dispatcher does not wait for the standalone pygemc test matrix. GEMC performs its own integration tests
before publishing updated images, and the downstream Deploy workflow runs only after those tests succeed.

## Workflow inventory

- [`pygemc_tests.yml`](pygemc_tests.yml) — **pygemc tests**
  - Trigger: non-Markdown pushes and pull requests targeting `main`.
  - Effect: installs pygemc with development dependencies and runs pytest on Python 3.10 and 3.14.
- [`trigger_src_tests.yml`](trigger_src_tests.yml) — **Trigger GEMC compatibility test**
  - Trigger: non-Markdown pushes to `main`.
  - Effect: dispatches `gemc/src` workflow `test_after_pygemc.yml` using `GEMC_SRC_PAT`.
  - Downstream: a successful GEMC compatibility test rebuilds GEMC and CLAS12 images and tarballs.
- [`publish_pypi.yml`](publish_pypi.yml) — **Publish PyPI**
  - Trigger: a published stable GitHub release or manual dispatch with a stable `vX.Y.Z` tag.
  - Effect: builds, verifies, and publishes the package to PyPI or TestPyPI through trusted publishing.
  - Authorization: uses the selected GitHub environment and OIDC `id-token: write`, not a PyPI API token.
- [`dev_release.yml`](dev_release.yml) — **Nightly Dev Release**
  - Trigger: daily at 01:34 UTC or manual dispatch.
  - Effect: moves the `dev` tag and recreates the development prerelease from generated notes.

## Cross-repository contract

The dispatcher URL in `trigger_src_tests.yml` names the target workflow file directly:

```text
gemc/src/.github/workflows/test_after_pygemc.yml
```

The target workflow's displayed name is `Test after pygemc`; the GEMC Deploy workflow uses that exact name in
its `workflow_run.workflows` list and pairs it with the `workflow_dispatch` event. Therefore:

- Renaming the target file requires updating `trigger_src_tests.yml` here.
- Renaming the displayed workflow requires updating `gemc/src/.github/workflows/deploy.yml`.
- A successful manual run of the target compatibility workflow on `main` is deployment-authorized.
- `GEMC_SRC_PAT` must retain permission to dispatch workflows in `gemc/src`.

## Permissions and published state

- `pygemc_tests.yml` only reads repository content through the default token permissions.
- `trigger_src_tests.yml` uses `GEMC_SRC_PAT` only for the cross-repository dispatch request.
- `publish_pypi.yml` uses OIDC trusted publishing and reads the selected stable tag.
- `dev_release.yml` writes the moving `dev` tag and GitHub prerelease through `GITHUB_TOKEN`.

Treat changes to the dispatcher, release, or PyPI workflows as changes to external published state.

## Safe workflow changes

When changing the GEMC compatibility entry point:

1. Add the new workflow file in `gemc/src` first.
2. Update this repository's dispatch URL.
3. Update the accepted workflow name in the GEMC Deploy workflow if the displayed name changed.
4. Remove the old entry point only after this caller is deployed.
5. Validate YAML, line wrapping, and `git diff --check` before pushing.

For a coordinated update of the full chain, publish `clas12-systems`, then `src`, then `pygemc`.

[src-workflows]: https://github.com/gemc/src/blob/main/.github/workflows/README.md
