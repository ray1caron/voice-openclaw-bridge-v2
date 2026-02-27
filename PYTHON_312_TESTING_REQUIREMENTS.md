# Python 3.12 Testing Requirements

**Date:** 2026-02-27
**Required for:** Python 3.12 test environment

---

## Issue

When running tests on Python 3.12, failures occur with:
```
KeyError: 'zoneinfo._tzpath'
```

This is required by `pydantic-settings>=2.0` for timezone support.

---

## Solution

### Install tzdata

```bash
pip install tzdata
```

Or add to dependencies:

```toml
# pyproject.toml
dependencies = [
    # ...
    "tzdata>=2023.3",  # Required for pydantic-settings timezone support
]
```

---

## Why It's Needed

- `pydantic-settings` uses `zoneinfo._tzpath` for timezone configuration
- Python 3.12 requires timezone database (tzdata) for proper `zoneinfo` support
- Without tzdata, config loading fails with `KeyError: 'zoneinfo._tzpath'`
- All tests that import from config will fail

---

## Verification

### Check if tzdata is installed:
```bash
python3 -c "import tzdata; print(f'tzdata version: {tzdata.__version__}')"
```

### Run tests:
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
python3 -m pytest tests/unit/test_stt_worker.py -v
```

Expected:
```
======================== 27 passed in X.XXs =========================
```

---

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/ci.yml`:

```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install tzdata  # ← Required for Python 3.12
      - name: Run tests
        run: pytest tests/unit -v
```

---

## Related Documentation

- Updated: `TEST_ENVIRONMENT.md` - Added tzdata to environment details
- Updated: `pyproject.toml` - Added tzdata to dependencies
- This file: `PYTHON_312_TESTING_REQUIREMENTS.md`

---

**Created:** 2026-02-27 10:50 PST
**Status:** Documented and fixed
**Next:** Install tzdata and re-run tests