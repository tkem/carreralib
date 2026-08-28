# carreralib

Python interface to Carrera® DIGITAL 124/132 slotcar systems, connected via
serial (cable) or Bluetooth LE (Carrera AppConnect®). Supports Python >= 3.10.

## Structure

- `src/carreralib/` — library package (`src` layout)
  - `cu.py` — `ControlUnit`, the main public API for talking to a Control Unit
  - `protocol.py` — low-level wire protocol: packing/unpacking, checksums
  - `connection.py` — abstract connection interface used by `ControlUnit`
  - `serial.py` — serial (pyserial) connection implementation
  - `ble.py` — Bluetooth LE connection implementation
  - `fw.py` — standalone firmware-update CLI (`python -m carreralib.fw`)
  - `__main__.py` — simple CLI / race management system (RMS) demo
  - `*.pyi` — type stubs for the public documented interface only
    (`__init__`, `cu`, `connection`, `protocol`); `serial.py`, `ble.py`,
    `fw.py`, `__main__.py` are undocumented/internal and have no stubs
  - `py.typed` — PEP 561 marker so type checkers pick up the stubs
- `tests/` — `unittest`-style tests (e.g. `test_protocol.py`)
- `docs/` — Sphinx documentation (reST, uses doctest)
- `.github/workflows/ci.yml` — CI: runs plain `tox` on CPython 3.10–3.14
  (including free-threaded builds) and PyPy

Note that `fw.py` and `__main__.py` do all their work at module level under
`if __name__ == "__main__"` / at import time; `__main__.py` in particular calls
`parser.parse_args()` on import, so it cannot be imported from a test.

## Conventions

- Public API is exported from `carreralib/__init__.py` (`ControlUnit`,
  `connection`, `protocol`); keep `__all__` in sync when adding public symbols.
- Docstrings use reST/Sphinx style (see `cu.py`), including tables for
  namedtuple field documentation. Follow this style for new public classes.
- Code style is enforced by `ruff` (both lint and format, see
  `[tool.ruff.lint]` in [pyproject.toml](../pyproject.toml)). Run
  `tox -e ruff` and `tox -e ruff-format` before considering changes complete.
- Response types (e.g. `ControlUnit.Status`, `ControlUnit.Timer`) are
  `collections.namedtuple` subclasses with `__slots__ = ()`.
- When adding or changing a public symbol in `__init__.py`, `cu.py`,
  `connection.py`, or `protocol.py`, update the matching `.pyi` stub in the
  same directory to keep it in sync. `pyright` is configured in
  `[tool.pyright]` in [pyproject.toml](../pyproject.toml).

## Workflow

This project uses `tox` for all checks; environments are defined in
[tox.ini](../tox.ini):

- `tox -e py` — run tests via `pytest` with coverage
- `tox -e pyright` — type-check with pyright
- `tox -e ruff` — lint with ruff
- `tox -e ruff-format` — check formatting with ruff
- `tox -e docs` — build Sphinx documentation
- `tox -e doctest` — run doctests in `docs/`
- `tox` (no args) — run the full default envlist

Always run checks through `tox`, never through bare `pytest`/`ruff`/`pyright`:
those tools are not installed system-wide, and `tox` builds an sdist and
installs the package into its own venv. Also note there is no system `python`
or `pip` — use `python3`/`pip3` for one-off scripting.

The first run of any `tox` environment needs network access to install its
dependencies from PyPI.

## Testing

- Tests live in `tests/` and use the standard library `unittest` module
  (`unittest.TestCase`), not `pytest`-style bare functions — follow this
  pattern for new tests.
- The runner is `pytest` with `pytest-cov`; coverage is reported for the
  *installed* package, so paths in the report point into
  `.tox/py/lib/pythonX.Y/site-packages/carreralib/`, not `src/`.
- Pass pytest arguments through tox, e.g.
  `tox -e py -- tests/test_protocol.py -k chksum`.
- No hardware is required or available: test `cu.py` and `connection.py`
  against a fake `connection.Connection` subclass with scripted
  `send()`/`recv()` behaviour rather than a real device.
- CI includes free-threaded CPython and PyPy, so do not write tests that
  depend on CPython refcounting semantics (e.g. deterministic `__del__`
  timing).

## Notes

- Hardware (serial cable, Bluetooth LE Control Unit) is not available in this
  environment, so changes to `serial.py`/`ble.py` cannot be tested against
  real devices; rely on `protocol.py` unit tests and code review instead.
- This is not an official Carrera® product; avoid implying official
  affiliation in docs or code comments.
