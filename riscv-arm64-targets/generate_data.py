import os
import re
import json
import datetime

# Configuration
ARM64_DIR = 'dtbs-list-arm64'
RISCV_DIR = 'dtbs-list-riscv'
OUTPUT_FILE = 'data.js'

# Kernel Release Dates (Year.Month)
# Sources: instructions.txt and Wikipedia for potentially missing ones
KERNEL_DATES = {
    'v4.1': '2015.06',
    'v4.4': '2016.01',
    'v4.9': '2016.12',
    'v4.14': '2017.11',
    'v4.19': '2018.10',
    'v5.4': '2019.11',
    'v5.10': '2020.12',
    'v5.15': '2021.10',
    'v6.1': '2022.12',
    'v6.6': '2023.10',
    'v6.12': '2024.11',
    'v6.18': '2025.11',
    'v6.19-rc3': '2025.12'
}

# Regex to match filename versions
# e.g., arm64.dtbs.v4.9 -> v4.9, riscv.dtbs.6.1 -> 6.1 (normalize to v6.1)
# Also handles occasional suffixes like .dtbs-check.v4.19
VERSION_REGEX = re.compile(r'.*\.dtbs(?:-check)?\.v?(\d+\.\d+(?:-rc\d+)?)')

# Regex to parse DTB lines
# DTC     arch/arm64/boot/dts/amlogic/meson-gxbb-odroidc2.dtb
# Vendor is usually the directory after dts/
DTC_REGEX = re.compile(r'\s*DTC\s+arch/(?:arm64|riscv)/boot/dts/([^/]+)/.*\.dtb')

def normalize_version(v_str):
    if not v_str.startswith('v'):
        return 'v' + v_str
    return v_str

def parse_files(directory, arch):
    data = {} # { version: { vendor: count, total: count } }
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return data

    for filename in os.listdir(directory):
        match = VERSION_REGEX.match(filename)
        if not match:
            continue
            
        version = normalize_version(match.group(1))
        filepath = os.path.join(directory, filename)
        
        counts = {}
        total = 0
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                dtc_match = DTC_REGEX.match(line)
                if dtc_match:
                    vendor = dtc_match.group(1)
                    counts[vendor] = counts.get(vendor, 0) + 1
                    total += 1
        
        # Only add valid data
        if total > 0:
            data[version] = {
                'vendors': counts,
                'total': total,
                'date': KERNEL_DATES.get(version, 'Unknown')
            }
            
    return data

def main():
    print("Parsing ARM64...")
    arm64_data = parse_files(ARM64_DIR, 'arm64')
    
    print("Parsing RISCV...")
    riscv_data = parse_files(RISCV_DIR, 'riscv')
    
    # Sort by version/date
    # Helper to sort versions loosely (major.minor)
    def version_key(v):
        # handle -rc
        clean_v = v.replace('v', '').split('-')[0]
        parts = list(map(int, clean_v.split('.')))
        return parts

    sorted_versions = sorted(list(set(list(arm64_data.keys()) + list(riscv_data.keys()))), key=version_key)
    
    final_output = {
        'labels': sorted_versions,
        'dates': [KERNEL_DATES.get(v, '') for v in sorted_versions],
        'arm64': [],
        'riscv': [],
        'vendors_list': set()
    }

    # Calculate "New Vendors" for RISCV and ARM64
    # Logic: For each version, find vendors that appear for the first time.
    
    seen_vendors_arm = set()
    seen_vendors_riscv = set()

    for v in sorted_versions:
        # ARM64
        if v in arm64_data:
            entry = arm64_data[v]
            current_vendors = set(entry['vendors'].keys())
            new_vs = list(current_vendors - seen_vendors_arm)
            entry['new_vendors'] = sorted(new_vs)
            seen_vendors_arm.update(current_vendors)
            
            final_output['arm64'].append(entry)
            for vendor in entry['vendors']:
                final_output['vendors_list'].add(vendor)
        else:
            final_output['arm64'].append(None)
            
        # RISCV
        if v in riscv_data:
             entry = riscv_data[v]
             current_vendors = set(entry['vendors'].keys())
             new_vs = list(current_vendors - seen_vendors_riscv)
             entry['new_vendors'] = sorted(new_vs)
             seen_vendors_riscv.update(current_vendors)
             
             final_output['riscv'].append(entry)
        else:
            final_output['riscv'].append(None)

    final_output['vendors_list'] = sorted(list(final_output['vendors_list']))

    # Write to JS file
    js_content = f"const KERNEL_DATA = {json.dumps(final_output, indent=2)};"
    with open(OUTPUT_FILE, 'w') as f:
        f.write(js_content)
    
    print(f"Data written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
