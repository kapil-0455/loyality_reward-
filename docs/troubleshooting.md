# Troubleshooting Log -- Day 3

This log records issues encountered during Day 3 implementation and the
fixes used.

## 1. `ModuleNotFoundError: No module named 'backend'`

**Symptom:** Running a nested test file directly by its path caused
Python to fail to import the `backend` package.

**Cause:** Direct execution of a nested test file can make the test
file's directory the import starting point rather than the project root.

**Fix:** Run tests from the project root using pytest as a module:

``` powershell
python -m pytest tests/unit/test_eligibility.py -v
```

If needed in the current PowerShell session, set the project root on
`PYTHONPATH`:

``` powershell
$env:PYTHONPATH = (Get-Location).Path
```

Empty `__init__.py` files were also added/checked in the relevant
package directories.

**Verification:** The eligibility tests were subsequently discovered and
passed.

## 2. Pytest reported `collected 0 items` / `no tests ran`

**Symptom:** Pytest started but did not find any tests in the file.

**Cause:** The file contained ordinary executable example code, but no
test functions whose names began with `test_`.

**Fix:** Convert the checks into pytest test functions, for example:

``` python
def test_inactive_customer():
    ...
    assert result["eligible"] is False
```

Then run the test module from the project root:

``` powershell
python -m pytest tests/unit/test_eligibility.py -v
```

**Verification:** Pytest discovered and passed the eligibility test
functions.

## 3. `services` directory did not exist

**Symptom:** The recommendation-service file path could not be used
because `backend/app/services/` had not yet been created.

**Cause:** The folder was part of the target project structure but had
not been created during the earlier domain/decision tasks.

**Fix:** Create the directory and package marker, then create the
service module:

``` text
backend/app/services/
├── __init__.py
└── reward_recommendation.py
```

**Verification:** The recommendation-service tests were subsequently
reported as passing.

## 4. Test execution convention

For consistency, run individual test modules or the complete suite from
the project root with:

``` powershell
python -m pytest tests/ -v
```

Do not use direct execution of nested test files as the normal project
test command.

## 5. Evidence and follow-up

The development session recorded successful runs for the Day 3 test
modules and the full test suite. Keep the local terminal output or test
report as evidence and record the exact passed/failed/skipped counts
from the pytest summary.

Do not add additional defects to this log unless they were actually
observed during development.
