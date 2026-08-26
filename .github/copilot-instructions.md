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
  - `fw.py` — firmware-related helpers
  - `__main__.py` — simple CLI / race management system (RMS) demo
  - `*.pyi` — type stubs for the public documented interface only
    (`__init__`, `cu`, `connection`, `protocol`); `serial.py`, `ble.py`,
    `fw.py`, `__main__.py` are undocumented/internal and have no stubs
  - `py.typed` — PEP 561 marker so type checkers pick up the stubs
- `tests/` — `unittest`-style tests (e.g. `test_protocol.py`)
- `docs/` — Sphinx documentation (reST, uses doctest)

## Conventions

- Public API is exported from `carreralib/__init__.py` (`ControlUnit`,
  `connection`, `protocol`); keep `__all__` in sync when adding public symbols.
- Docstrings use reST/Sphinx style (see `cu.py`), including tables for
  namedtuple field documentation. Follow this style for new public classes.
- Code style is enforced by `ruff` (both lint and format, see
  `[tool.ruff.lint]` in [pyproject.toml](../pyproject.toml)). Run `ruff check`
  and `ruff format` before considering changes complete.
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

Tests live in `tests/` and use the standard library `unittest` module
(`unittest.TestCase`), not `pytest`-style bare functions — follow this
pattern for new tests.

## Notes

- Hardware (serial cable, Bluetooth LE Control Unit) is not available in this
  environment, so changes to `serial.py`/`ble.py` cannot be tested against
  real devices; rely on `protocol.py` unit tests and code review instead.
- This is not an official Carrera® product; avoid implying official
  affiliation in docs or code comments.
