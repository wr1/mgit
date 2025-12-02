# multig

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
uv run multig --help
```

Or after installation:

```bash
multig --help
```

## Configuration

Create a `.multigrc` YAML file in your project root.

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
```