# Kernel Database Generator

## Overview

`generate-rva23-coverage.py` is a Python script that **automatically generates** the `rva23-coverage-data.json` database by:

1. Fetching all available kernel tags from kernel.org (v6.5+)
2. Downloading and parsing `extensions.yaml` and `cpus.yaml` for each version
3. Analyzing RVA23 mandatory extension support
4. Generating a complete JSON database file

**No more manual work!** This replaces the manual "copy from browser console" workflow.

## Prerequisites

```bash
# Python 3.7 or later
python3 --version

# Install PyYAML (required)
pip3 install pyyaml
```

## Usage

### Basic Usage (Auto-detect all versions)

```bash
cd rva23/
python3 generate-rva23-coverage.py
```

This will:
- Auto-detect **all available kernel versions >= 6.5** (including patch releases like 6.12.1, 6.12.2, etc.)
- Analyze each one (can be 300+ versions!)
- Generate `rva23-coverage-data.json`

**Note**: Analyzing all versions can take 5-10 minutes. For faster results, use `--major-only` flag.

### Analyze Only Major Versions (Recommended)

```bash
python3 generate-rva23-coverage.py --major-only
```

This analyzes only major versions (6.5, 6.6, 6.7, etc.) and skips patch releases (6.5.1, 6.5.2, etc.). Much faster!

### Analyze Specific Versions

```bash
# Major versions
python3 generate-rva23-coverage.py --versions 6.10,6.11,6.12

# Specific patch releases
python3 generate-rva23-coverage.py --versions 6.12.1,6.12.2,6.12.3
```

### Custom Output File

```bash
python3 generate-rva23-coverage.py --output my-database.json
```

### Get Help

```bash
python3 generate-rva23-coverage.py --help
```

## Example Output

### With --major-only flag (Recommended)

```
Found 10 kernel versions >= 6.5 (including patch releases)
Filtered to 10 major versions only
============================================================
Generating kernel database for 10 versions
============================================================

Analyzing v6.5...
  Fetching extensions.yaml... ✓ (145 extensions)
  Fetching cpus.yaml... ✓ (87 extensions)
  Coverage: 48% (28/58)
  U64: 48% (16/33)
  S64: 48% (12/25)

Analyzing v6.6...
  Fetching extensions.yaml... ✓ (148 extensions)
  Fetching cpus.yaml... ✓ (89 extensions)
  Coverage: 52% (30/58)
  U64: 52% (17/33)
  S64: 52% (13/25)

...

============================================================
Writing database to rva23-coverage-data.json...
✓ Successfully generated database
  Versions: 10 successful, 0 failed
  Coverage range: 48% (v6.5) to 82% (v6.12)
  Output: rva23-coverage-data.json
============================================================
Done! You can now use the database in rva23-kernel-support-evolution.html
============================================================
```

### Without --major-only (All Versions)

```
Found 328 kernel versions >= 6.5 (including patch releases)
============================================================
Generating kernel database for 328 versions
============================================================

Analyzing v6.5...
  ... (same as above)

Analyzing v6.5.1...
  ... 

... (takes 5-10 minutes for all 328 versions)
```

## Features

### ✅ Advantages

1. **Fully Automated**: No manual copying from browser console
2. **Accurate**: Direct from kernel.org, no human transcription errors
3. **Repeatable**: Re-run anytime to update with new kernel versions
4. **Fast**: Analyzes 8 versions in ~10-20 seconds (network speed dependent)
5. **Incremental**: Can analyze specific versions without redoing all
6. **Validated**: Ensures math is correct (coverage %, counts, etc.)

### 🔍 What It Does

For each kernel version, the script:

1. **Fetches YAML files** from kernel.org stable git repo
2. **Parses extension strings** using PyYAML
3. **Checks 58 mandatory extensions** (33 U64 + 25 S64)
4. **Detects support** via keyword matching (same logic as kernel-compare.html)
5. **Handles special cases** (e.g., Zic64b via block-size properties)
6. **Calculates statistics** (coverage %, supported/missing lists)
7. **Generates JSON** in the exact format needed by kernel-compare.html

## Output Format

The generated `rva23-coverage-data.json` will have:

```json
{
  "_metadata": {
    "description": "...",
    "last_updated": "2024-12-13",
    "data_structure_version": "1.0",
    "versions_included": ["6.5", "6.6", "6.7", ...],
    "coverage_range": "48% (v6.5) to 82% (v6.12)",
    "generator": "generate-rva23-coverage.py"
  },
  "versions": {
    "6.5": { ... },
    "6.6": { ... },
    ...
  }
}
```

Each version entry contains all the data needed by `kernel-compare.html`:
- Coverage percentages
- Supported/missing extension lists
- U64 and S64 breakdowns

## Updating the Database

### When a New Kernel Version is Released

```bash
# Option 1: Re-run with auto-detect (will find new versions)
python3 generate-rva23-coverage.py

# Option 2: Add just the new version
python3 generate-rva23-coverage.py --versions 6.13
# Then manually merge into existing rva23-coverage-data.json

# Option 3: Specify range including new version
python3 generate-rva23-coverage.py --versions 6.5,6.6,6.7,6.8,6.9,6.10,6.11,6.12,6.13
```

### Incremental Updates

To add a single version to existing database:

```bash
# Generate data for new version only
python3 generate-rva23-coverage.py --versions 6.13 --output temp-6.13.json

# Manually merge the "6.13" entry from temp-6.13.json into rva23-coverage-data.json
# Update _metadata fields (last_updated, versions_included, coverage_range)
```

## Troubleshooting

### Import Error: No module named 'yaml'

```bash
pip3 install pyyaml
```

### Connection Timeout

The script has a 10-second timeout per file. If you have slow internet:

1. Try again (network might be temporarily slow)
2. Analyze fewer versions at once
3. Check firewall/proxy settings

### Version Not Found (404 Error)

This means the version doesn't exist in the kernel.org git repo:
- v6.13 might not be released yet
- v6.4 and earlier don't have `extensions.yaml`
- Typo in version number

### YAML Parse Error

Rare, but if YAML structure changes:
- Check the kernel.org file manually
- Report as an issue (file format may have changed)

## Integration with kernel-compare.html

Once you generate `rva23-coverage-data.json`:

1. **Replace the existing empty database** with the generated one
2. **Open `rva23-kernel-support-evolution.html`** in browser
3. **Select any version** from the dropdown
4. **Click "Analyze Version"** - it will load **instantly** from the database!

Evolution analysis will also be near-instant for all versions in the database.

## Validation

The script automatically validates:
- Total mandatory extensions = 58 (always)
- U64 total = 33 (always)
- S64 total = 25 (always)
- Coverage % math is correct
- Supported + Missing = Total

You can also validate the generated file using the Node.js script from `DATABASE-STATUS.md`.

## Maintenance

### Updating RVA23 Extension List

If the RVA23 profile changes (unlikely, as it's ratified):

1. Edit the extension definitions in `rva23-profile-extensions.json`
2. Update both "RVA23U64" and "RVA23S64" sections
3. Re-run the script to regenerate the database

### Adding Special Checks

For extensions that need special detection logic (like Zic64b):

```python
# In the analyze_version() function, add special check:
if not supported and ext.get("special_check") == "your_check_name":
    if your_condition_here:
        supported = True
```

## License

This script is part of the RVA23 Profile Coverage Analyzer toolset.

