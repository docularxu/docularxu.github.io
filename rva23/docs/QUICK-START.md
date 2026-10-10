# Quick Start Guide

## Generate the Complete Database

### One Command Solution (Recommended)

```bash
cd rva23/
python3 generate-rva23-coverage.py --major-only --no-verify-ssl
```

This will:
1. Auto-detect all **major** kernel versions >= 6.5 (6.5, 6.6, 6.7, etc.)
2. Fetch and analyze each version from kernel.org
3. Generate `kernel-data.json` with complete, accurate data
4. Take ~30-60 seconds for 8-10 versions

### Refresh an Existing Database (Recommended for Updates)

```bash
cd rva23/
python3 generate-rva23-coverage.py --update
```

This keeps every version already in `rva23-coverage-data.json`, fetches only
the tags kernel.org has added since, and drops `-rc` entries of a series once
its final release exists. `-rc` tags are included only for the cycle still in
development, so the page always ends at the newest mainline tag.

### All Versions (Including Patch Releases)

```bash
cd rva23/
python3 generate-rva23-coverage.py --no-verify-ssl
```

This analyzes **all 300+ versions** including patch releases (6.5.1, 6.5.2, 6.12.4, etc.). Takes 5-10 minutes!

### Use the Database

Once generated, simply:
1. Open `rva23-kernel-support-evolution.html` in your browser
2. Select any version → **Instant results!**
3. Run evolution analysis → **Completes in < 1 second!**

## Why This Approach?

| Method | Speed | Accuracy | Effort |
|--------|-------|----------|--------|
| **Manual (old way)** | Slow (5-10s per version) | Error-prone | High |
| **Python Script (new)** | Fast (1-2s per version) | 100% accurate | Zero |

### Benefits

✅ **Automated** - No manual copying  
✅ **Accurate** - Direct from kernel.org  
✅ **Fast** - Batch processing  
✅ **Repeatable** - Re-run anytime for updates  
✅ **Validated** - Math checked automatically  

## Prerequisites

```bash
# Check Python version (need 3.7+)
python3 --version

# Install required dependencies
pip3 install pyyaml
```

## That's It!

After running the script once, you have a complete, accurate database that makes the web tool lightning-fast!

