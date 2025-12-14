# Complete Usage Guide

## Quick Reference

```bash
# Most common usage (recommended)
python3 generate-rva23-coverage.py --major-only --no-verify-ssl

# All versions (300+ versions, takes 5-10 minutes)
python3 generate-rva23-coverage.py --no-verify-ssl

# Specific versions
python3 generate-rva23-coverage.py --versions 6.12.1,6.12.2,6.12.3 --no-verify-ssl
```

## Understanding the Options

### `--major-only` (Recommended)

**What it does**: Only analyzes major kernel releases (6.5, 6.6, 6.7, etc.)

**When to use**: 
- ✅ For the web tool (kernel-compare.html) - major versions are sufficient
- ✅ For evolution charts - patch releases don't add new extensions
- ✅ When you want results fast (< 1 minute for ~10 versions)

**Example**:
```bash
python3 generate-rva23-coverage.py --major-only --no-verify-ssl
```

**Output**: ~10-15 major versions, ~30-60 seconds

### Without `--major-only` (All Versions)

**What it does**: Analyzes ALL kernel releases including patches (6.5, 6.5.1, 6.5.2, 6.12.4, etc.)

**When to use**:
- 🔍 Research purposes - complete historical data
- 📊 Detailed analysis of when specific extensions were added
- 🎯 Specific patch release analysis

**Example**:
```bash
python3 generate-rva23-coverage.py --no-verify-ssl
```

**Output**: 300+ versions, 5-10 minutes

### `--versions` (Custom Selection)

**What it does**: Analyzes only the versions you specify

**When to use**:
- Adding specific new releases to existing database
- Testing a subset of versions
- Analyzing specific patch releases

**Examples**:
```bash
# Test with a single version
python3 generate-rva23-coverage.py --versions 6.12 --no-verify-ssl

# Analyze a range of recent versions
python3 generate-rva23-coverage.py --versions 6.10,6.11,6.12,6.13 --no-verify-ssl

# Analyze specific patch releases
python3 generate-rva23-coverage.py --versions 6.12.1,6.12.2,6.12.3 --no-verify-ssl
```

### `--output` (Custom Output File)

**What it does**: Specifies where to save the JSON database

**Default**: `rva23-coverage-data.json`

**When to use**:
- Testing without overwriting existing database
- Creating separate databases for different purposes
- Backing up before regenerating

**Example**:
```bash
python3 generate-rva23-coverage.py --major-only --output backup-$(date +%Y%m%d).json --no-verify-ssl
```

### `--no-verify-ssl` (SSL Bypass)

**What it does**: Disables SSL certificate verification

**When to use**:
- Getting SSL certificate errors
- Corporate proxies blocking certificates
- macOS certificate issues

**Note**: Only use if getting SSL errors, otherwise omit this flag

## Performance Comparison

| Mode | Versions | Time | Use Case |
|------|----------|------|----------|
| `--major-only` | ~10-15 | 30-60s | ✅ **Recommended** for web tool |
| All versions | 300+ | 5-10min | Research/complete data |
| `--versions 6.12` | 1 | 2-3s | Quick test |
| `--versions 6.5,6.12` | 2 | 5s | Specific comparison |

## Common Workflows

### Initial Setup (First Time)

```bash
cd rva23/

# Install dependency
pip3 install pyyaml

# Generate database with major versions
python3 generate-rva23-coverage.py --major-only --no-verify-ssl

# Open web tool
open rva23-kernel-support-evolution.html
```

### Update Database (New Kernel Released)

```bash
# Option 1: Add just the new version
python3 generate-rva23-coverage.py --versions 6.13 --output temp-6.13.json --no-verify-ssl
# Then manually merge into rva23-coverage-data.json

# Option 2: Regenerate entire database (recommended)
python3 generate-rva23-coverage.py --major-only --no-verify-ssl
```

### Research / Complete Analysis

```bash
# Generate complete database with all patch releases
python3 generate-rva23-coverage.py --output rva23-coverage-data-complete.json --no-verify-ssl

# This will take 5-10 minutes but gives you every single release
```

### Test Specific Versions

```bash
# Test a few versions before full generation
python3 generate-rva23-coverage.py --versions 6.10,6.11,6.12 --output test.json --no-verify-ssl

# Verify the output looks correct
cat test.json | python3 -m json.tool | head -50
```

## Troubleshooting

### SSL Certificate Errors

```
Error: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solution**: Add `--no-verify-ssl` flag

### PyYAML Not Found

```
ERROR: PyYAML is required
```

**Solution**: `pip3 install pyyaml`

### Version Not Found (404)

```
Failed to fetch extensions.yaml: HTTP 404
```

**Cause**: The version doesn't exist or doesn't have extensions.yaml (pre-6.5)

**Solution**: Only use versions >= 6.5

### Too Slow

```
Taking forever to analyze...
```

**Solution**: Use `--major-only` flag or specify fewer versions with `--versions`

## Expected Results

### v6.5 (Early Release)
- Coverage: ~48% (28/58)
- Missing: Many newer extensions

### v6.12 (Recent Release)
- Coverage: ~64% (37/58) 
- Better support but still missing some S64 extensions

### Future Versions
- Coverage should gradually increase as more extensions are added to kernel

## Next Steps

After generating the database:

1. **Open `rva23-kernel-support-evolution.html`** in your browser
2. **Select any version** from the dropdown
3. **Results appear instantly** (loaded from database)
4. **Run Evolution Analysis** to see trends across versions

No more waiting for network fetches! 🚀

