# Code Review — carreralib

**Date:** 2026-09-01
**Scope:** full source tree (`src/carreralib/`), stubs, tests, tox/CI config
**Test status:** `tox -e py` → 3 passed, **27% total coverage**
(`protocol.py` 78%, `cu.py` 41%, `connection.py` 50%,
`serial.py`/`ble.py`/`fw.py`/`__main__.py` 0%)

All findings below were reproduced against the actual code, not inferred.

## Type Stubs (`__init__.pyi`, `connection.pyi`, `cu.pyi`, `protocol.pyi`)

Signatures, return types, and re-exports match their implementations. One
*documentation* divergence remains: `cu.pyi` correctly declares
`Status.pit: tuple[bool, ...]`, but the `cu.py` docstring still describes it as
an "8-bit pit lane bit mask" (see finding 3).

## Code — Correctness

| # | Severity | Location | Finding |
|---|----------|----------|---------|
| 1 | High | `__main__.py` L118 | `self.logger.warning("Unknown data from CU: " + data)` runs exactly when `ControlUnit.poll()` returned `None`, so the concatenation raises `TypeError` and kills the curses UI. Fix: `self.logger.warning("Unknown data from CU: %r", data)`. *(Carried over from the 2026-08-28 review — still unfixed.)* |
| 2 | Medium | `protocol.py` L4–9 | `ChecksumError` inherits from `Exception`, **not** from `ProtocolError`, despite `ProtocolError`'s docstring claiming to be "the base class of all protocol exceptions". Verified: `issubclass(ChecksumError, ProtocolError)` is `False`. `ProtocolError` is in fact never raised anywhere in the codebase, so callers cannot write `except protocol.ProtocolError`. Fix `protocol.py` and `protocol.pyi` together. |
| 3 | Medium | `cu.py` L27 | `Status.pit` is documented as "8-bit pit lane bit mask", but `poll()` L124 converts the mask to `tuple(... for n in range(8))`, i.e. a tuple of 8 `bool`s — as the stub, `README.rst`, and `docs/index.rst` all show. The docstring is wrong. Likewise `Status.fuel` is documented as an "Eight-item list" but is a `tuple`. |
| 4 | Medium | `ble.py` L68 | `self.__input` is a `queue.Queue`, but the `put_nowait` call is guarded by `except asyncio.QueueFull`. A `queue.Queue` raises `queue.Full`, so the handler can never fire. Latent today (the queue is unbounded), but it becomes a silent crash the moment a `maxsize` is introduced. |
| 5 | Low | `connection.py` L20–21 | `Connection.__del__` unconditionally calls `self.close()`. If a subclass `__init__` raises before setting up its resource (e.g. `SerialConnection` when `serial_for_url()` fails), `close()` touches an unset attribute and Python prints an `Exception ignored in: ... __del__` traceback. Reproduced. Guard `close()` or drop `__del__` in favour of the existing `contextlib.closing` usage. |
| 6 | Low | `cu.py` L118–121 | The `?:` status fallback tries `"2x8YYYBYC"` and, on `ChecksumError`, retries with `"2x8YYYBYxxC"`. Checksums are only 4 bits, so a long-firmware frame has a ~1-in-16 chance of *passing* the short-format checksum and being silently mis-parsed (`display` and `pit` taken from the wrong offsets). Discriminating on `len(res)` would be deterministic. |
| 7 | Low | `cu.py` L134–146 | `request()` loops `while True` over `recv()` with no attempt limit, relying entirely on the connection timeout to break out. A device emitting a steady stream of unrelated messages spins forever. Also, when `recv()` returns falsy the method logs a warning and returns the empty buffer, which callers (`poll()`, `version()`) translate into `None` — the two `# TODO: raise?` comments mark this as unresolved. |

## Code — Robustness & API Consistency

| # | Severity | Location | Finding |
|---|----------|----------|---------|
| 8 | Medium | `protocol.py` `unpack()` | Truncated buffers raise a bare `IndexError`, not a protocol exception. Verified: `unpack("cYYC", b"J1")` → `IndexError: list index out of range`. Every `_unpack_*` helper indexes `values[offset + i]` without a length check. Since these bytes come off the wire, this is the most likely real-world failure mode and it surfaces opaquely. |
| 9 | Medium | `protocol.py` `pack()` | Too few arguments raises `StopIteration` from `next(argiter)`. Verified: `pack("ccC", b"J")` → `StopIteration`. Inside a generator that would silently terminate iteration rather than error. Should be `ValueError`/`TypeError`. |
| 10 | Low | `protocol.py` L44, L63 | The two pre-existing `# TODO: check all args/buf used` are still open, and both are observable: `pack("cC", b"J", b"X")` silently drops the extra argument, and `unpack("cC", b"J0EXTRA")` silently ignores the trailing bytes. |
| 11 | Low | `protocol.py` `_pack_C` | The parameter is named `offset`, but `pack()` passes the format's repeat `count` into it (`_PACK_FORMATS[conv](buf, argiter, count)`). The `C` specifier therefore repurposes the count as "start the checksum at byte N" — a genuinely useful feature discoverable only from `test_protocol.py`. Rename the parameter and add a one-line comment. A related edge case falls out of this: `unpack("0YC", b"0")` raises `ValueError: size is negative` from `chksum`. |
| 12 | Low | `protocol.py` L26 | `chksum` slices before wrapping: `memoryview(buf[offset:offset+size]).tolist()`. The slice copies; `memoryview(buf)[offset:offset+size]` preserves the zero-copy intent. |
| 13 | Low | `protocol.py` `_pack_s` | `arg.ljust(count, ...)[:count]` silently truncates over-long input: `pack("2s", b"abcdef")` → `b"ab"`. Padding short input is intended; truncating long input probably masks a caller bug. |
| 14 | Low | `serial.py` L28–38, `ble.py` L105–115 | The offset/size validation in `send()` is duplicated verbatim in both backends (and mirrored again in `protocol.chksum`). Factor it into a helper on `Connection` to prevent drift. |
| 15 | Info | `connection.py` L1–11 | `ConnectionError` and `TimeoutError` shadow the builtins of the same name, and neither derives from its builtin counterpart, so `except TimeoutError` behaves differently depending on which name is in scope. Deriving from the builtins would be backward-compatible and friendlier. |
| 16 | Info | `cu.py` L88–93 | `ControlUnit.__init__` adopts a caller-supplied `Connection`, but `close()` closes it unconditionally — `ControlUnit` takes ownership of an object it did not create. Worth documenting explicitly. |
| 17 | Info | `ble.py` L88–92 | A connect timeout in `BleakThread.start()` raises but leaves the thread running with no way to stop it; a later `close()` → `stop()` would also hit an unset `self.__loop`. |
| 18 | Info | `ble.py` L38–50 | `BleakThread.send()` swallows `RuntimeError` when the loop is not running, with no log record. Failures are invisible to callers. |
| 19 | Info | `cu.py` L36, L60 | Docstring typos: "fule mode" → "fuel mode"; "milleseconds" → "milliseconds". |

## Design & Security Notes

- **Untrusted device strings (informational).** `connection.open()` routes
  anything that is not a 6-part colon MAC or 5-part dash UUID to
  `serial.serial_for_url()`, which supports `socket://host:port` and
  `rfc2217://` handlers. An attacker-controlled device string therefore opens
  arbitrary outbound TCP connections. Not a concern for the documented
  operator-supplied use case, but it should stay documented as an assumption.
- **Device-type heuristic.** Verified routing: `AA:BB:CC:DD:EE:FF` and
  `12345678-1234-1234-1234-123456789abc` → BLE; `/dev/ttyUSB0`, `COM3`,
  `hwgrep://Carrera`, `socket://host:1234` → serial. The behaviour is correct
  but entirely implicit and currently untested.
- **Import-time side effects.** `__main__.py` calls `parser.parse_args()` at
  module scope, so the module cannot be imported at all under pytest (it would
  consume pytest's own `sys.argv` and then `sys.exit`). This single line is
  what pins `__main__.py` at 0% coverage, and it also makes `RMS`,
  `formattime`, and `posgetter` — all pure, easily testable logic —
  unreachable from tests.

## Tests — Gaps and Suggested Improvements

Current suite: one file, three test methods, all in `tests/test_protocol.py`,
covering only the happy path of `chksum`/`pack`/`unpack`. Run everything with
`tox -e py` (arguments pass through, e.g. `tox -e py -- -k chksum`).

### Structural improvements

| # | Priority | Suggestion |
|---|----------|------------|
| T1 | High | **Add a shared fake `Connection`.** A ~10-line `connection.Connection` subclass taking a scripted list of `recv()` responses and recording `send()` calls unlocks essentially all of `cu.py` without hardware. Verified working: it round-trips both a `Status` frame (`b"?:>>>>>>>>060088"`) and a `Timer` frame through `poll()`. Put it in `tests/__init__.py` or `tests/fakes.py` so `test_cu.py` and a future `test_connection.py` share it. |
| T2 | High | **Use `subTest`.** The existing tests loop over table-driven cases with plain `assertEqual`, so the first failure hides every later case and the message does not say which row failed. Wrapping each row in `with self.subTest(fmt=fmt, buf=buf):` is a one-line change with a large debugging payoff. |
| T3 | Medium | **Make `__main__.py` testable.** Moving the argparse/curses block into a `main()` called from `if __name__ == "__main__":` (mirroring the guard `fw.py` already uses) would let tests import `RMS`, `formattime`, and `posgetter`. That alone would catch finding 1. |
| T4 | Low | **Consider a coverage floor.** CI already installs `coverage` and uploads to Codecov but enforces no threshold. Once `cu.py`/`protocol.py` coverage rises, `--cov-fail-under` would prevent regressions. |

### `test_protocol.py` — cases worth adding

| # | Target | Case |
|---|--------|------|
| P1 | `unpack` | Truncated buffers for every specifier (`Y`, `B`, `I`, `s`, `C`) — pins down finding 8. Today they raise `IndexError`; the test should assert whatever exception the fix settles on. |
| P2 | `unpack` | `ChecksumError` on a corrupted frame (e.g. `b"J60911"`). Today the only error path in `protocol.py` exercised at all is indirect, via `cu.poll()`'s fallback. |
| P3 | `pack` | Too few arguments (finding 9) and extra unused arguments (finding 10). |
| P4 | `pack` | Range validation for `B`, `I`, `Y`, `r`: `-1` and one-past-max each. The `_pack_I`/`_pack_B` bounds checks are currently uncovered (report lines 90–101, 108). |
| P5 | `pack` | `'c'` with a non-`bytes` or multi-byte argument, and `'s'` with a non-`bytes` argument — both `TypeError`/`ValueError` branches are uncovered. |
| P6 | `pack`/`unpack` | Invalid conversion character (`"Q"`) → `ValueError`, in both directions. |
| P7 | `chksum` | The four `ValueError` guards (negative offset, `offset > len`, negative size, `offset + size > len`) — lines 16/18/22/24 are all uncovered. |
| P8 | `pack`/`unpack` | Round-trip property: for each documented format, `unpack(fmt, pack(fmt, *args)) == args`. Cheap, and it catches nibble-order regressions in `_pack_I`/`_unpack_I`, whose swapped-nibble layout is the least obvious code in the module. |
| P9 | `pack`/`unpack` | The `C`-with-count offset behaviour (finding 11) and the `unpack("0YC", ...)` edge case, so the intended semantics are locked in before any refactor. |
| P10 | `unpack` | Accept `bytearray`/`memoryview` as well as `bytes`: `unpack` calls `memoryview(buf).tolist()` but `_unpack_c`/`_unpack_s` slice `buf` directly, so the element type of the result varies with the input type. |

### New `tests/test_cu.py` — cases worth adding

| # | Target | Case |
|---|--------|------|
| C1 | `poll()` | Status frame → `Status` with the expected `fuel` tuple, `start`, `mode`, 8-bool `pit` tuple, and `display`. Also pins finding 3's real contract. |
| C2 | `poll()` | Timer frame → `Timer`, and specifically that `address` is decremented by one (`b"?2..."` → `address == 1`). This off-by-one is invisible in the current suite. |
| C3 | `poll()` | Both `?:` variants — with and without the two trailing unknown bytes — to pin the firmware-compatibility fallback (finding 6). |
| C4 | `poll()`/`version()` | Empty response → `None`, the current documented-by-omission behaviour at the two `# TODO: raise?` sites. Guards against accidental change. |
| C5 | `request()` | Unexpected messages are skipped until one matching the sent command byte arrives, and `send()` received exactly the expected wire bytes. |
| C6 | `setword()` | All four `ValueError` guards: word > 31, address > 7, value > 15, repeat outside 1..15, plus the negative cases. |
| C7 | `setlap()` | Range check, and that it splits into `setlap_hi(value >> 4)` / `setlap_lo(value & 0xF)` — assert on the two frames captured by the fake connection. |
| C8 | `setpos()`/`clrpos()` | Position out of range raises; `clrpos()` emits `setword(6, 0, 9)`. |
| C9 | `setspeed`/`setbrake`/`setfuel` | Each emits the right word index with `repeat=2` — a table-driven test over `(method, word)` pairs. |
| C10 | `fwu_write()` | Both branches: `max_fwu_block_size is None` (single `E` frame) and a fake connection with `max_fwu_block_size = 18` (chunked `F` frames plus a terminating `E`). This block-splitting logic exists nowhere else and is entirely uncovered. |
| C11 | `press()`/`start()` | `start()` presses `START_ENTER_BUTTON_ID`; the button-ID constants map to the expected `T` frames. |
| C12 | `close()` | Delegates to the underlying connection (finding 16). |

### New `tests/test_connection.py` — cases worth adding

| # | Target | Case |
|---|--------|------|
| N1 | `open()` | Table-driven dispatch check over the device strings under "Device-type heuristic" above, with `carreralib.ble`/`carreralib.serial` patched so no hardware and no `bleak` import is needed. Pure string logic. |
| N2 | `Connection` | `recv()`/`send()` raise `NotImplementedError` on the base class. |
| N3 | `Connection` | Exception hierarchy: `BufferTooShort` and `TimeoutError` are subclasses of `connection.ConnectionError` (and, once finding 2 is fixed, the analogous assertion for `protocol.ChecksumError`/`ProtocolError`). Cheap, and catches accidental base-class changes. |
| N4 | `Connection.__del__` | A subclass whose `__init__` raises must not emit an ignored-exception traceback (finding 5). **Note:** the CI matrix includes free-threaded CPython and PyPy, so this must not rely on refcount-based finalisation — drive it with an explicit `gc.collect()`, or assert on `close()` directly rather than on finaliser timing. |
| N5 | `SerialConnection` | `recv()` framing (accumulate until `$` or `#`, `TimeoutError` on empty read, `BufferTooShort` past `maxlength`) and `send()` framing (`"` prefix, `$` suffix, flush) against a stubbed `serial_for_url`. No hardware needed — only the pyserial API surface is mocked. |
| N6 | `BLEConnection` | `recv()`'s command-byte reconstruction heuristic (`$`-terminated; `len == 6` → `b"0"` prefix, else `b"?"`) against a stubbed `BleakThread`. This is the subtlest untested logic in the BLE path, and it is pure byte manipulation. |

## Summary

The protocol/connection/`ControlUnit` core is sound and the public stubs are
accurate. Highest-value fixes, in order: the `__main__.py` `TypeError` crash
(finding 1), the broken `ProtocolError` hierarchy (finding 2), the `Status.pit`
docstring (finding 3), and turning wire-level `IndexError`/`StopIteration`
leaks into proper protocol exceptions (findings 8 and 9).

On testing, the single highest-leverage step is T1 — a shared fake
`Connection`. It is a few lines of code, needs no hardware, and is the
prerequisite for the ~12 `cu.py` cases above, which together would take the
main public API from 41% to near-complete coverage.
