#!/usr/bin/env python3
"""
RVA23 Profile Coverage Database Generator

This script automatically:
1. Loads RVA23 profile definitions (mandatory + optional extensions) from rva23-profile-extensions.json
2. Fetches all stable kernel tags (v6.5+) from kernel.org
3. Downloads and parses extensions.yaml and cpus.yaml for each version
4. Analyzes both mandatory AND optional extension support for RVA23U64 and RVA23S64
5. Generates/updates rva23-coverage-data.json database file

Usage:
    python3 generate-rva23-coverage.py [--versions 6.5,6.6,6.7] [--output rva23-coverage-data.json]
"""

import argparse
import json
import re
import ssl
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip3 install pyyaml")
    sys.exit(1)


def load_rva23_profile(profile_file: str = "rva23-profile-extensions.json") -> Dict:
    """Load RVA23 profile definitions from JSON file."""
    profile_path = Path(__file__).parent / profile_file
    
    if not profile_path.exists():
        print(f"ERROR: Profile file not found: {profile_path}")
        sys.exit(1)
    
    with open(profile_path, 'r') as f:
        return json.load(f)


def build_extension_mapping(profile_data: Dict) -> Dict[str, List[Dict]]:
    """
    Build extension mapping with keyword search patterns.
    Returns: {
        "RVA23U64_mandatory": [...],
        "RVA23U64_optional": [...],
        "RVA23S64_mandatory": [...],
        "RVA23S64_optional": [...]
    }
    """
    
    # Keyword mapping for special cases
    KEYWORD_MAP = {
        # Base ISA
        "M": ["m"],
        "A": ["a"],
        "F": ["f"],
        "D": ["d"],
        "C": ["c"],
        "B": ["b", "zba", "zbb", "zbc", "zbs"],
        "V": ["v"],
        "H": ["h"],
        # Special cases
        "Svbare": ["svbare", "riscv,none"],
        "Sv39": ["sv39", "riscv,sv39"],
        "Sv48": ["sv48", "riscv,sv48"],
        "Sv57": ["sv57", "riscv,sv57"],
        "Ssstateen": ["ssstateen", "smstateen"],
        "Supm": ["supm", "smnpm", "ssnpm"],
        "Zic64b": ["zic64b"],  # Special block size check
    }
    
    extension_groups = {}
    
    for profile_name, profile_info in profile_data["profiles"].items():
        # Process mandatory extensions
        mandatory = []
        for ext in profile_info.get("mandatory", []):
            name = ext["name"]
            keywords = KEYWORD_MAP.get(name, [name.lower()])
            
            entry = {
                "name": name,
                "keywords": keywords,
                "status": "Mandatory",
                "history": ext.get("history", "")
            }
            
            if name == "Zic64b":
                entry["special_check"] = "block_size"
            
            mandatory.append(entry)
        
        extension_groups[f"{profile_name}_mandatory"] = mandatory
        
        # Process mandatory_hypervisor extensions (for RVA23S64)
        if "mandatory_hypervisor" in profile_info:
            for ext in profile_info["mandatory_hypervisor"]:
                name = ext["name"]
                keywords = KEYWORD_MAP.get(name, [name.lower()])
                
                mandatory.append({
                    "name": name,
                    "keywords": keywords,
                    "status": "Mandatory (Hypervisor)",
                    "history": ext.get("history", "")
                })
        
        # Process optional extensions
        optional = []
        for ext in profile_info.get("optional", []):
            name = ext["name"]
            keywords = KEYWORD_MAP.get(name, [name.lower()])
            
            optional.append({
                "name": name,
                "keywords": keywords,
                "status": ext.get("status", "Optional"),
                "history": ext.get("history", "")
            })
        
        extension_groups[f"{profile_name}_optional"] = optional
    
    return extension_groups


def fetch_url(url: str, timeout: int = 10, verify_ssl: bool = True) -> str:
    """Fetch content from URL with timeout."""
    req = Request(url, headers={'User-Agent': 'RVA23-Coverage-Analyzer/1.0'})
    
    # Handle SSL verification
    context = None
    if not verify_ssl:
        context = ssl._create_unverified_context()
    
    try:
        with urlopen(req, timeout=timeout, context=context) as response:
            return response.read().decode('utf-8')
    except (URLError, HTTPError) as e:
        raise Exception(f"Failed to fetch {url}: {e}")


def get_kernel_tags(verify_ssl: bool = True) -> List[str]:
    """Get all kernel tags from git.kernel.org."""
    print("Fetching kernel tags from git.kernel.org...")
    
    url = "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/refs/tags"
    
    try:
        content = fetch_url(url, verify_ssl=verify_ssl)
        
        # Parse HTML to extract tags
        tags = []
        for line in content.split('\n'):
            match = re.search(r"tag/\?h=v(6\.\d+(?:\.\d+)?)'?>v(6\.\d+(?:\.\d+)?)</a>", line)
            if match:
                tag = match.group(2)
                tags.append(tag)
        
        # Filter: all versions >= 6.5
        valid_tags = []
        seen = set()
        
        for tag in tags:
            if tag in seen:
                continue
                
            parts = tag.split('.')
            if len(parts) >= 2:
                major, minor = int(parts[0]), int(parts[1])
                
                if major == 6 and minor >= 5:
                    valid_tags.append(tag)
                    seen.add(tag)
        
        # Sort by version
        def version_key(v):
            parts = v.split('.')
            while len(parts) < 3:
                parts.append('0')
            return tuple(map(int, parts[:3]))
        
        valid_tags.sort(key=version_key)
        
        print(f"Found {len(valid_tags)} kernel versions >= 6.5")
        return valid_tags
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("Falling back to manual version list...")
        return ["6.5", "6.6", "6.7", "6.8", "6.9", "6.10", "6.11", "6.12", "6.13", "6.14", "6.15", "6.16", "6.17", "6.18"]


def parse_yaml_for_extensions(yaml_content: str) -> Tuple[Set[str], Set[str]]:
    """Parse YAML and extract extension strings and properties."""
    extensions = set()
    properties = set()
    
    try:
        doc = yaml.safe_load(yaml_content)
        
        def search_recursively(obj):
            if obj is None:
                return
            
            if isinstance(obj, dict):
                # Check for const values
                if 'const' in obj and isinstance(obj['const'], str):
                    extensions.add(obj['const'].lower())
                
                # Check for enum values
                if 'enum' in obj and isinstance(obj['enum'], list):
                    for val in obj['enum']:
                        if isinstance(val, str):
                            extensions.add(val.lower())
                
                # Check for properties
                if 'properties' in obj and isinstance(obj['properties'], dict):
                    properties.update(obj['properties'].keys())
                
                # Recurse into all values
                for value in obj.values():
                    search_recursively(value)
            
            elif isinstance(obj, list):
                for item in obj:
                    search_recursively(item)
        
        search_recursively(doc)
        
    except yaml.YAMLError as e:
        print(f"  Warning: YAML parse error: {e}")
    
    return extensions, properties


def check_extension_support(ext: Dict, all_extensions: Set[str], all_properties: Set[str]) -> bool:
    """Check if an extension is supported."""
    # Check standard keywords
    for keyword in ext["keywords"]:
        if keyword.lower() in all_extensions:
            return True
    
    # Special check for Zic64b (block size properties)
    if ext.get("special_check") == "block_size":
        if any(prop in all_properties for prop in 
               ['riscv,cbom-block-size', 'riscv,cboz-block-size']):
            return True
    
    return False


def analyze_version(version: str, extension_groups: Dict, verify_ssl: bool = True) -> Optional[Dict]:
    """Analyze a specific kernel version for all RVA23 extensions."""
    print(f"\nAnalyzing v{version}...")
    
    base_url = "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain/Documentation/devicetree/bindings/riscv"
    files = ['extensions.yaml', 'cpus.yaml']
    
    all_extensions = set()
    all_properties = set()
    
    # Fetch and parse YAML files
    for filename in files:
        url = f"{base_url}/{filename}?h=v{version}"
        print(f"  Fetching {filename}...", end=' ')
        
        try:
            content = fetch_url(url, verify_ssl=verify_ssl)
            extensions, properties = parse_yaml_for_extensions(content)
            all_extensions.update(extensions)
            all_properties.update(properties)
            print(f"✓ ({len(extensions)} extensions)")
        except Exception as e:
            print(f"✗ {e}")
            return None
    
    # Analyze each profile's extensions
    results = {}
    
    for group_name, extensions in extension_groups.items():
        supported_list = []
        missing_list = []
        
        for ext in extensions:
            is_supported = check_extension_support(ext, all_extensions, all_properties)
            
            if is_supported:
                supported_list.append(ext["name"])
            else:
                missing_list.append(ext["name"])
        
        results[group_name] = {
            "supported": supported_list,
            "missing": missing_list,
            "supportedCount": len(supported_list),
            "totalCount": len(extensions),
            "coveragePercent": round((len(supported_list) / len(extensions)) * 100) if extensions else 0
        }
    
    # Calculate aggregate statistics
    u64_mandatory = results["RVA23U64_mandatory"]
    u64_optional = results["RVA23U64_optional"]
    s64_mandatory = results["RVA23S64_mandatory"]
    s64_optional = results["RVA23S64_optional"]
    
    # Overall mandatory coverage (U64 + S64)
    total_mandatory = u64_mandatory["totalCount"] + s64_mandatory["totalCount"]
    total_mandatory_supported = u64_mandatory["supportedCount"] + s64_mandatory["supportedCount"]
    overall_mandatory_coverage = round((total_mandatory_supported / total_mandatory) * 100) if total_mandatory else 0
    
    # Overall optional coverage (U64 + S64)
    total_optional = u64_optional["totalCount"] + s64_optional["totalCount"]
    total_optional_supported = u64_optional["supportedCount"] + s64_optional["supportedCount"]
    overall_optional_coverage = round((total_optional_supported / total_optional) * 100) if total_optional else 0
    
    print(f"  RVA23U64 Mandatory: {u64_mandatory['coveragePercent']}% ({u64_mandatory['supportedCount']}/{u64_mandatory['totalCount']})")
    print(f"  RVA23U64 Optional:  {u64_optional['coveragePercent']}% ({u64_optional['supportedCount']}/{u64_optional['totalCount']})")
    print(f"  RVA23S64 Mandatory: {s64_mandatory['coveragePercent']}% ({s64_mandatory['supportedCount']}/{s64_mandatory['totalCount']})")
    print(f"  RVA23S64 Optional:  {s64_optional['coveragePercent']}% ({s64_optional['supportedCount']}/{s64_optional['totalCount']})")
    print(f"  Overall Mandatory:  {overall_mandatory_coverage}% ({total_mandatory_supported}/{total_mandatory})")
    print(f"  Overall Optional:   {overall_optional_coverage}% ({total_optional_supported}/{total_optional})")
    
    return {
        "version": version,
        "overallMandatoryCoverage": overall_mandatory_coverage,
        "overallOptionalCoverage": overall_optional_coverage,
        "totalMandatory": total_mandatory,
        "totalOptional": total_optional,
        "RVA23U64": {
            "mandatory": u64_mandatory,
            "optional": u64_optional
        },
        "RVA23S64": {
            "mandatory": s64_mandatory,
            "optional": s64_optional
        }
    }


def generate_database(versions: List[str], extension_groups: Dict, output_file: str, verify_ssl: bool = True):
    """Generate the complete database file."""
    print(f"\n{'='*70}")
    print(f"Generating RVA23 coverage database for {len(versions)} versions")
    print(f"{'='*70}")
    
    database = {
        "_metadata": {
            "description": "RVA23 Profile Coverage Data - Mandatory and Optional Extensions",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "data_structure_version": "1.0",
            "note": "This database tracks both mandatory and optional extension support across kernel versions",
            "source": "rva23-profile-extensions.json",
            "versions_included": [],
            "generator": "generate-rva23-coverage.py",
            "extension_counts": {
                "RVA23U64_mandatory": len(extension_groups.get("RVA23U64_mandatory", [])),
                "RVA23U64_optional": len(extension_groups.get("RVA23U64_optional", [])),
                "RVA23S64_mandatory": len(extension_groups.get("RVA23S64_mandatory", [])),
                "RVA23S64_optional": len(extension_groups.get("RVA23S64_optional", []))
            }
        },
        "versions": {}
    }
    
    successful = []
    failed = []
    
    for version in versions:
        result = analyze_version(version, extension_groups, verify_ssl=verify_ssl)
        if result:
            database["versions"][version] = result
            successful.append(version)
        else:
            failed.append(version)
    
    if successful:
        # Update metadata
        database["_metadata"]["versions_included"] = successful
        
        # Calculate coverage trends
        mandatory_coverages = [database["versions"][v]["overallMandatoryCoverage"] for v in successful]
        optional_coverages = [database["versions"][v]["overallOptionalCoverage"] for v in successful]
        
        min_mandatory = min(mandatory_coverages)
        max_mandatory = max(mandatory_coverages)
        min_optional = min(optional_coverages)
        max_optional = max(optional_coverages)
        
        database["_metadata"]["coverage_summary"] = {
            "mandatory": f"{min_mandatory}% to {max_mandatory}%",
            "optional": f"{min_optional}% to {max_optional}%"
        }
        
        # Write to file
        print(f"\n{'='*70}")
        print(f"Writing database to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(database, f, indent=2)
        
        print(f"✓ Successfully generated database")
        print(f"  Versions: {len(successful)} successful, {len(failed)} failed")
        print(f"  Mandatory coverage: {database['_metadata']['coverage_summary']['mandatory']}")
        print(f"  Optional coverage: {database['_metadata']['coverage_summary']['optional']}")
        print(f"  Output: {output_file}")
        
        if failed:
            print(f"\n  Failed versions: {', '.join(failed)}")
    else:
        print("\nERROR: No versions were successfully analyzed")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate RVA23 profile coverage database (mandatory + optional extensions)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze major versions only (recommended, fast)
  python3 generate-rva23-coverage.py --major-only --no-verify-ssl

  # Analyze all versions including patch releases
  python3 generate-rva23-coverage.py --no-verify-ssl

  # Analyze specific versions
  python3 generate-rva23-coverage.py --versions 6.10,6.11,6.12 --no-verify-ssl

  # Specify custom profile file and output
  python3 generate-rva23-coverage.py --profile custom-profile.json --output custom-db.json --no-verify-ssl
        """
    )
    
    parser.add_argument(
        '--versions',
        help='Comma-separated list of versions to analyze (e.g., 6.5,6.6,6.7)',
        default=None
    )
    
    parser.add_argument(
        '--major-only',
        action='store_true',
        help='Only include major versions (6.x, not 6.x.y)',
        default=False
    )
    
    parser.add_argument(
        '--profile',
        help='Path to RVA23 profile JSON file (default: rva23-profile-extensions.json)',
        default='rva23-profile-extensions.json'
    )
    
    parser.add_argument(
        '--output',
        help='Output JSON file path (default: rva23-coverage-data.json)',
        default='rva23-coverage-data.json'
    )
    
    parser.add_argument(
        '--no-verify-ssl',
        action='store_true',
        help='Disable SSL certificate verification',
        default=False
    )
    
    args = parser.parse_args()
    
    # Load RVA23 profile
    print("Loading RVA23 profile definitions...")
    profile_data = load_rva23_profile(args.profile)
    extension_groups = build_extension_mapping(profile_data)
    
    print(f"Loaded extension groups:")
    for group_name, extensions in extension_groups.items():
        print(f"  {group_name}: {len(extensions)} extensions")
    
    # Determine versions to analyze
    verify_ssl = not args.no_verify_ssl
    if args.no_verify_ssl:
        print("\nWarning: SSL verification disabled")
    
    if args.versions:
        versions = [v.strip() for v in args.versions.split(',')]
        print(f"\nAnalyzing specified versions: {', '.join(versions)}")
    else:
        versions = get_kernel_tags(verify_ssl=verify_ssl)
        
        if args.major_only:
            major_versions = []
            seen = set()
            for v in versions:
                parts = v.split('.')
                if len(parts) >= 2:
                    major_minor = f"{parts[0]}.{parts[1]}"
                    if major_minor not in seen:
                        major_versions.append(major_minor)
                        seen.add(major_minor)
            versions = major_versions
            print(f"Filtered to {len(versions)} major versions only")
    
    if not versions:
        print("ERROR: No versions to analyze")
        sys.exit(1)
    
    # Generate database
    generate_database(versions, extension_groups, args.output, verify_ssl=verify_ssl)
    
    print(f"\n{'='*70}")
    print("Done! Database ready for analysis and visualization.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
