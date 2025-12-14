import re
import subprocess
import os
import json
import sys

LINUX_REPO = "/Volumes/Linux.git/linux.git"
TARGET_REF = "remotes/linus/master"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Updated path since script is now in rva23/
HTML_FILE = os.path.join(SCRIPT_DIR, "linux-kernel-coverage.html")

ALIASES = {
    "Svbare": ["riscv,none"],
    "Ssstateen": ["smstateen"],
    "Sha": ["h"],
    "Supm": ["supm", "smnpm", "ssnpm"],
    "Zic64b": ["riscv,cbom-block-size"],
    "Ssnpm": ["ssnpm", "smnpm"],
    "Zabha": ["zabha"],
    "Sdtrig": ["sdtrig"],
    "Ssstrict": ["ssstrict"],
    "Sspm": ["sspm"],
    "Zicfilp": ["zicfilp"],
    "Zicfiss": ["zicfiss"],
    "Zama16b": ["zama16b"],
    "Ziccif": ["ziccif"],
    "Ziccamoa": ["ziccamoa"],
    "Zicclsm": ["zicclsm"],
    "Za64rs": ["za64rs"],
    "Ss1p13": ["ss1p13"],
}

def get_extensions_from_html(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    matches = re.findall(r'name:\s*"([^"]+)"', content)
    seen = set()
    unique_exts = []
    for m in matches:
        if m not in seen:
            unique_exts.append(m)
            seen.add(m)
    return unique_exts

def find_commit(extension, repo_path, ref):
    ext_lower = extension.lower()
    
    files = [
        "Documentation/devicetree/bindings/riscv/extensions.yaml",
        "Documentation/devicetree/bindings/riscv/cpus.yaml",
    ]
    
    search_terms = []
    
    if extension in ALIASES:
        for alias in ALIASES[extension]:
            search_terms.append(f"const: {alias}")
            search_terms.append(f"\"{alias}\"")
            search_terms.append(f"- {alias}")
            if "," in alias:
                 search_terms.append(alias)
    
    search_terms.extend([
        f"const: {ext_lower}",
        f"\"{ext_lower}\"",
        f"- {ext_lower}",
    ])
    
    if len(ext_lower) == 1:
        search_terms = [f"\"{ext_lower}\"", f"const: {ext_lower}"]
    
    if ext_lower.startswith("sv"):
         search_terms.append(f"riscv,{ext_lower}")

    for file_path in files:
        for term in search_terms:
            cmd = [
                "git", "-C", repo_path, "log", ref, "-S" + term, 
                "--reverse", "--format=%H", "--", file_path
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    commits = result.stdout.strip().split('\n')
                    commit_hash = commits[0]
                    
                    details_cmd = [
                        "git", "-C", repo_path, "show", "--format=%s|%b", "-s", commit_hash
                    ]
                    details_res = subprocess.run(details_cmd, capture_output=True, text=True)
                    subject_body = details_res.stdout
                    
                    lore_match = re.search(r'(https?://lore\.kernel\.org/[^\s]+)', subject_body)
                    lore_link = lore_match.group(1) if lore_match else None
                    if lore_link:
                        lore_link = lore_link.rstrip('.,)>]')

                    return {
                        "extension": extension,
                        "commit_id": commit_hash,
                        "github_url": f"https://github.com/torvalds/linux/commit/{commit_hash}",
                        "lore_url": lore_link,
                        "file_found": file_path,
                        "term_found": term
                    }
            except Exception as e:
                pass
                
    return None

def main():
    extensions = get_extensions_from_html(HTML_FILE)
    print(f"Searching {len(extensions)} extensions in {TARGET_REF}...", file=sys.stderr)
    
    results = []
    for ext in extensions:
        info = find_commit(ext, LINUX_REPO, TARGET_REF)
        if info:
            results.append(info)
        else:
            results.append({
                "extension": ext,
                "error": "Not found"
            })
            
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()

