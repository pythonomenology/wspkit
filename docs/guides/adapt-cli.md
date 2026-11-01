# Adapt an existing CLI

The Config_File flow exists so that a tool with a working CLI can
expose itself over WSP without writing any Python glue. This page
walks through that case end to end, using Hatch as the worked
example.

> **A note on Hatch.** This page describes how Hatch *could* adapt
> itself today, with no code changes on Hatch's part — purely by
> shipping a config file. Hatch itself plans to integrate with wspkit
> directly via a `hatch server` subcommand, which is a different and
> tighter integration. The Config_File approach below is the path for
> any tool author who wants to expose their CLI via WSP without
> taking a runtime dependency.

## Goal

Expose Hatch's environment management over WSP, so that a consuming
tool (`wsp`, an editor, an LSP-style client, anything) can call:

- `environment/list` → `hatch env show --json`
- `environment/create` → `hatch env create`
- `environment/delete` → `hatch env remove`
- `environment/execute` → `hatch run -e <env> -- <command>`

…without Hatch importing wspkit or writing a single Python adapter.

## The config file

```toml
# hatch-wsp.toml

[handlers."environment/list"]
command = ["hatch", "env", "show", "--json"]
result = "json"

[handlers."environment/create"]
command = ["hatch", "env", "create", "{name}"]
result = "template"
template = { id = "{name}", name = "{name}", python_version = "{python_version}", interpreter_path = "", installed_packages = [], extra = {} }

[handlers."environment/delete"]
command = ["hatch", "env", "remove", "{id}"]
result = "template"
template = { id = "{id}" }

[handlers."environment/execute"]
command = ["hatch", "run", "-e", "{id}", "--", "{argv}"]
result = "exec"
```

That's it. Six declarations, no Python. Run it with:

```sh
python -m wspkit --config hatch-wsp.toml
```

Or drive a single call through the CLI:

```sh
wsp --config hatch-wsp.toml environment/create --name scratch --python-version 3.12
```

## Walking through each endpoint

### `environment/list` → `hatch env show --json`

Hatch's `env show` already accepts a `--json` flag and emits a JSON
object describing the configured environments. The `result = "json"`
mode tells wspkit to parse stdout as JSON and return it verbatim.

There's a wrinkle: Hatch's JSON shape is keyed by environment name
and includes Hatch-specific fields, while WSP wants an array of
`Environment` objects with WSP's field names. If the shape doesn't
match, the wspkit server's response will technically be valid JSON but
won't match the WSP schema. That's the boundary to understand:

- **If Hatch's JSON happens to match WSP's** (it doesn't, today) →
  ship the config above and you're done.
- **If it doesn't** → fall back to an `import` handler that calls
  `hatch env show --json`, transforms the shape, and returns the
  WSP-formatted array. See "Where the boundary breaks" below.

### `environment/create` → `hatch env create`

`hatch env create scratch` doesn't print the created environment's
metadata to stdout. So `result = "json"` would fail — wspkit would try
to parse an empty stdout as JSON and raise `EXECUTION_FAILED`.

`result = "template"` is the right tool: wspkit synthesizes the WSP
result from the request params themselves.

```toml
[handlers."environment/create"]
command = ["hatch", "env", "create", "{name}"]
result = "template"
template = { id = "{name}", name = "{name}", python_version = "{python_version}", interpreter_path = "", installed_packages = [], extra = {} }
```

When the user calls
`wsp --config hatch-wsp.toml environment/create --name scratch --python-version 3.12`:

1. wspkit renders the argv: `hatch env create scratch`.
2. Hatch runs and exits 0.
3. wspkit synthesizes the result from the request params and the
   template:

   ```json
   {
     "id": "scratch",
     "name": "scratch",
     "python_version": "3.12",
     "interpreter_path": "",
     "installed_packages": [],
     "extra": {}
   }
   ```

The `interpreter_path` is empty because we don't know it without
running another Hatch query. WSP's contract permits that — clients
that need the interpreter call `environment/get` afterwards.

### `environment/delete` → `hatch env remove`

Same pattern as `create`: Hatch's `env remove` doesn't print
anything useful, so we synthesize a `DeleteAck` from the request:

```toml
[handlers."environment/delete"]
command = ["hatch", "env", "remove", "{id}"]
result = "template"
template = { id = "{id}" }
```

### `environment/execute` → `hatch run -e <env> -- <argv>`

Hatch can run a command inside one of its environments via
`hatch run -e <env> -- <command...>`. WSP's `environment/execute`
takes an `argv` array; the `{argv}` token in `command` splats the
array into multiple argv positions:

```toml
[handlers."environment/execute"]
command = ["hatch", "run", "-e", "{id}", "--", "{argv}"]
result = "exec"
```

A WSP request with
`{"id": "scratch", "argv": ["python", "-V"]}` becomes:

```
hatch run -e scratch -- python -V
```

`result = "exec"` tells wspkit to capture the subprocess's exit code,
stdout, and stderr and return them as the WSP `ExecuteResult`. The
subprocess's exit code is the value the caller cares about; wspkit
does **not** treat a non-zero exit as a failure here.

## Where the boundary breaks

The Config_File flow handles tools whose data model is already close
to WSP's. It struggles when:

### Field names disagree

WSP's `Environment` has `python_version`. Hatch's JSON likely has
`python` (or no version field at all on `env show`). Wspkit's
templating doesn't have rename/transform primitives.

**Fix:** an `import` handler that calls Hatch and renames fields:

```toml
[handlers."environment/list"]
import = "hatch_wsp.handlers.list_envs"
```

```python
# hatch_wsp/handlers.py
import json, subprocess

def list_envs(_params):
    proc = subprocess.run(
        ["hatch", "env", "show", "--json"],
        capture_output=True,
        check=True,
    )
    raw = json.loads(proc.stdout)
    return [
        {
            "id": name,
            "name": name,
            "python_version": cfg.get("python", "unknown"),
        }
        for name, cfg in raw.items()
    ]
```

### The result needs data the CLI doesn't print

`environment/get` is supposed to return `installed_packages`. Hatch
doesn't emit that on its own; you'd have to call
`hatch run -e <env> -- pip list --format=json` and parse the result.
That's two subprocess invocations and a transformation — beyond what
the Config_File flow can express.

**Fix:** an `import` handler that orchestrates the multi-step lookup.

### Conditional flags

`hatch env create scratch -p 3.12` only includes `-p 3.12` when the
user actually supplied a Python version. The Config_File flow has
no notion of "include this flag conditionally."

**Fix:** an `import` handler that builds argv programmatically.

## Mixing the two

You can mix `command` and `import` entries in the same Config_File:

```toml
# Easy methods get the subprocess flow.
[handlers."environment/create"]
command = ["hatch", "env", "create", "{name}"]
result = "template"
template = { id = "{name}", name = "{name}", python_version = "{python_version}", interpreter_path = "", installed_packages = [], extra = {} }

[handlers."environment/delete"]
command = ["hatch", "env", "remove", "{id}"]
result = "template"
template = { id = "{id}" }

[handlers."environment/execute"]
command = ["hatch", "run", "-e", "{id}", "--", "{argv}"]
result = "exec"

# The hard ones get a small Python adapter.
[handlers."environment/list"]
import = "hatch_wsp.handlers.list_envs"

[handlers."environment/get"]
import = "hatch_wsp.handlers.get_env"
```

This is usually the practical sweet spot: 80% of methods are
expressible declaratively, the remainder go through a small Python
module the tool author owns.
