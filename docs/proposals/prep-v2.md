# Technical Proposal — `mgit prep` v2: Truly Magical Context Folding

## Current Limitations (`prep` v1)
- Only accepts **one** string → treated as profile/alias or single repo name  
- No glob/wildcard support inside the argument  
- No way to say “fold everything that touches `b3_2d` **or** `b3_drp`” in one command  
- No automatic dependency resolution beyond what’s in `.mgitrc` aliases  
- Always folds **all** `*.py` files in the selected repos → noisy when you only care about one module

## Goal for v2
Make `mgit prep` the single smartest context-gathering command you ever type — so smart that you can literally paste the command straight into a Grok/Claude prompt and get perfect context 99 % of the time.

### New Invocation Examples (all must work)
```bash
# 1. Classic — profile/alias expansion (already works)
mgit prep 2d

# 2. Multiple targets (OR logic)
mgit prep b3_2d b3_drp cgfoil

# 3. Wildcards / globs directly in the argument line
mgit prep "b3_2d/**.py" "cgfoil/src/cgfoil/mesh/*.py"

# 4. Mixed globs + profiles + repo names
mgit prep 2d "b3_drp/tests/**_test.py" b3_geo

# 5. File-level precision (exact paths are allowed)
mgit prep src/b3_2d/mesher.py src/cgfoil/constrain.py

# 6. Smart auto-expansion: if a path exists in multiple repos → include all matches
mgit prep tests/test_airfoil.py          # finds it in b3_2d + cgfoil automatically

# 7. Negative exclusion (optional but extremely useful)
mgit prep b3_2d --exclude "**/__pycache__/**" "**/tests/**"

# 8. Dependency-aware mode (the real magic)
mgit prep b3_2d --with-deps           # automatically pulls b3m + cgfoil + b3_geo if imports are detected
```

## Proposed Implementation Plan

### 1. New CLI signature (still treeparse, zero boilerplate)
```python
command(
    name="prep",
    help="Magical context folding — the killer feature",
    callback=prep,
    arguments=[
        argument("targets", nargs="*", help="Repos, profiles, globs, or exact files"),
    ],
    options=[
        option("--exclude", "-x", multiple=True, help="Patterns to exclude"),
        option("--with-deps", "-d", action="store_true", help="Follow Python imports to add dependencies"),
        option("--max-files", type=int, default=200, help="Safety limit"),
        option("--output", "-o", type=str, default="__mgit_context.json"),
    ],
)
```

### 2. Core Resolution Algorithm (executed in order)
```text
for each token in targets:
    if token in config.profiles → expand to list
    elif token in config.aliases → expand recursively
    elif token contains wildcard (*, **) → treat as pathlib.rglob pattern
    elif Path(token).exists() → treat as exact file
    else → assume repo name (fallback)
→ merge all into a set of repo roots + a list of explicit Path objects
```

### 3. Optional `--with-deps` magic
- Run a very fast static import scanner (using `treeparse`’s own import finder or `pydeps`)
- For every file that is about to be folded:
  - extract `import b3_geo`, `from cgfoil import ...` etc.
  - map module name → repo via a tiny hardcoded + configurable map in `.mgitrc`
  - automatically add the corresponding repo (or specific file) if not already included

Example `.mgitrc` addition:
```yaml
import_map:
  b3_geo: b3_geo
  b3_msh: b3_msh
  cgfoil: cgfoil
  statesman: statesman
```

### 4. Final file selection
```python
files = set()
for repo in resolved_repos:
    files.update(repo.rglob("*.py"))          # default
for explicit_path in explicit_paths:
    files.add(explicit_path.resolve())
for pattern in user_globs:
    for repo in all_repos:
        files.update(repo.rglob(pattern))

# apply exclusions
for excl in excludes:
    files = {f for f in files if not fnmatch(f, excl)}
```

### 5. Output formats (user choice)
- Default: full cfold JSON (`__mgit_context.json`)
- `--format txt` → simple cfold-style text with headers
- `--format clip` → only copy to clipboard, no file
- Always print summary table:
```
Selected 87 files from 4 repos (21 k tokens) → __mgit_context.json
Copied to clipboard ✔
```

## Bonus Ideas (v2.1)
- `mgit prep --diff` → only files changed vs main branch
- `mgit prep --focus <function-name>` → fold only files containing that symbol (using `ripgrep` + `tree-sitter`)
- `mgit prep --chat` → directly opens Cursor/Continue with exactly these files indexed

## Result
After this change, the workflow becomes:
```bash
# You think: “I need to refactor the 2D mesher and its drape integration”
mgit prep b3_2d b3_drp --with-deps
# → 68 perfect files in clipboard, ready for Grok/Claude/Cursor
```

Zero manual folding ever again. This is the “magic” we actually want.

**Status:** Ready to implement in < 250 LOC. Say “do it” and I’ll ship the full patch.
