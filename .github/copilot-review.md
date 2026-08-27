# General code review

Ad-hoc review of the `carreralib` codebase (types, correctness, style,
security, docs). Not auto-generated from a specific tool run; see also
`tox -e pyright` / `tox -e ruff` for the automated checks these findings
complement.

## Bugs

### High: crash on unrecognized CU response in the demo CLI

[__main__.py](../src/carreralib/__main__.py#L113-L118) in `RMS.run()`:

```python
data = self.cu.poll()
...
elif isinstance(data, ControlUnit.Timer):
    self.handle_timer(data)
else:
    self.logger.warning("Unknown data from CU: " + data)
```

`ControlUnit.poll()` ([cu.py](../src/carreralib/cu.py#L128)) can legitimately
return `None` (`return None  # TODO: raise?`). When that happens here,
`"..." + data` raises `TypeError: can only concatenate str (not "NoneType")
to str)`, crashing the whole `curses` UI. The `data == last` short-circuit
only hides this while `poll()` keeps returning the same value across
iterations. Fix: use `%r`/`%s`-style formatting instead of `+`, e.g.
`self.logger.warning("Unknown data from CU: %r", data)`.

### Medium: BLE connect timeout leaks a running background thread

[ble.py](../src/carreralib/ble.py#L88-L92), `BLEConnection.__init__`:

```python
def __init__(self, address, timeout=1.0):
    self.__thread = t = BleakThread(address)
    self.__timeout = timeout
    t.start()
```

`BleakThread.start()` raises `TimeoutError` if the BLE connection isn't
established in time, but by then the thread is already running
`main()` (which has no timeout of its own around `BleakClient(...)`
connect). If `__init__` raises, the partially constructed `BLEConnection`
is discarded, but the background thread is not — it keeps trying to
connect indefinitely with no way to stop it (nothing retains a reference
to call `stop()`/`join()`). Consider passing a timeout into `BleakClient`
and/or stopping the thread before re-raising on timeout.

## Design / maintainability notes

- `Connection.send()`'s offset/size bounds-checking
  ([serial.py](../src/carreralib/serial.py#L28-L38),
  [ble.py](../src/carreralib/ble.py#L105-L115)) is duplicated verbatim in
  both connection implementations. It could be factored into a shared
  helper (e.g. on the `Connection` base class in
  [connection.py](../src/carreralib/connection.py)) to avoid drift between
  the two.
- `BleakThread.send()` ([ble.py](../src/carreralib/ble.py#L38-L50)) silently
  swallows a `RuntimeError` when the loop isn't running instead of logging
  it; failures there would be invisible to callers/logs.
- `ControlUnit.request()` ([cu.py](../src/carreralib/cu.py#L128-L143))
  retries `recv()` in an unbounded `while True` loop whenever a reply
  doesn't start with the expected command byte. This relies entirely on
  the underlying connection's own timeout to bound the loop; a
  misbehaving device that keeps sending unrelated messages could keep
  this spinning. Likely fine given the hardware use case, but worth a
  comment noting the assumption.
- `protocol.pack`/`protocol.unpack` ([protocol.py](../src/carreralib/protocol.py#L27-L60))
  have `# TODO: check all args used` / `# TODO: check all buf used`
  comments acknowledging that extra/unused arguments or trailing buffer
  bytes aren't validated — pre-existing, flagged by the original author,
  still open.
- The checksum-offset behavior of the `C` format specifier (e.g. a leading
  digit in `"2xC"` means "start the checksum at buffer offset 2", used to
  exclude a leading command byte) is non-obvious from the code alone and
  only really explained by the test cases in
  [test_protocol.py](../tests/test_protocol.py). A short comment near
  `_pack_C`/`_unpack_C` in [protocol.py](../src/carreralib/protocol.py)
  would help future readers.

## Type stubs (`.pyi`)

All four public stub files (`connection.pyi`, `cu.pyi`, `protocol.pyi`,
`__init__.pyi`) were checked line-by-line against their implementations
this session: signatures, return types, and re-exports all match, and
`pyright`/`ruff check`/`ruff format` are clean against them. No further
action needed there.

## Security notes (informational, not vulnerabilities in this context)

- [connection.py](../src/carreralib/connection.py)'s `open()` picks a
  transport based on the shape of the `device` string, ultimately calling
  `serial.serial_for_url()` for anything that isn't BLE-address-shaped.
  `serial_for_url` supports handlers like `socket://host:port` and
  `rfc2217://`, which means an attacker-controlled `device` string could
  make the process open arbitrary outbound TCP connections. Not an issue
  for the documented use case (operator-supplied local device strings),
  but relevant if `device` were ever sourced from untrusted/remote input.

## Test coverage gaps

Current `tox -e py` coverage run shows `cu.py` at ~41% and `connection.py`
at ~50%, with `serial.py`/`ble.py`/`fw.py`/`__main__.py` at 0% (expected —
hardware/CLI, can't run in this environment). Candidates for additional
*pure-logic* unit tests that don't need real hardware, using a small fake
`Connection` stub:

- `ControlUnit.poll()` response parsing (`Status` vs `Timer` vs `None`,
  including the two-branch checksum fallback for `?:`-prefixed replies).
- `ControlUnit.setword`/`setlap`/`setpos` argument validation
  (`ValueError` on out-of-range `word`/`address`/`value`/`repeat`/`position`).
- `ControlUnit.version()`'s `None` fallback when `request()` returns an
  empty response.

## Summary

The core protocol/type-stub layer (`protocol.py`, `connection.py`,
`cu.py`, and their `.pyi` stubs) is solid and well-covered by tests. The
packaging metadata copy/paste mistakes have been fixed. Remaining open
issues are the `__main__.py` crash bug and the BLE thread resource-leak
gap described above.
