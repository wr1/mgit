# mgit

A lightweight, LLM-transparent CLI tool for painless daily development on projects that consist of many independent git repositories (a "monorepo in spirit, polyrepo in practice").

## Installation

Using uv (recommended):

```bash
uv pip install -e .
```

Or with pip:

```bash
pip install -e .
```

## Usage

```bash
uv run mgit --help
```

Or after installation:

```bash
mgit --help
```

## Configuration

Create a `.mgitrc` YAML file in your project root.

Example:

```yaml
project_name: b3m-suite

profiles:
  code:
    - b3m
    - b3_geo
    - b3_msh
  ci:
    - b3m
    - b3_geo
    - b3_msh
    - b3_drp

aliases:
  2d: [b3_2d, cgfoil]
  core: [b3m, b3_geo, b3_msh]

import_map:
  b3_geo: b3_geo
  b3_msh: b3_msh
  cgfoil: cgfoil
  statesman: statesman

topics:
  2d-meshing:
    targets:
      - b3_2d:src/b3_2d/core/
      - b3_2d:src/b3_2d/cli/commands/*{mesh,anba}*
      - b3_2d:src/b3_2d/state/b3_2d_mesh.py
      - cgfoil:src/cgfoil/core/
      - cgfoil:src/cgfoil/models/airfoil_mesh.py
      - b3m:**/*{mesh,anba,2d}*.py
      - b3m:src/b3m/cli/steps.py
    exclude:
      - "**/tests/**"
      - "**/examples/**"
      - "**/__pycache__/**"
    with_deps: true
    max_files: 280
    include_summary: true

  bem:
    targets:
      - b3_bem:**/*.py
      - b3_geo:src/b3_geo/core/blade.py
    with_deps: true
    include_summary: true
```