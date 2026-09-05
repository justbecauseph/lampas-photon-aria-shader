import os
import re
import sys

def validate():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    shaders_dir = os.path.join(repo_root, "shaders")
    world0_dir = os.path.join(shaders_dir, "world0")
    aria_dir = os.path.join(shaders_dir, "aria")
    props_path = os.path.join(shaders_dir, "shaders.properties")

    assert os.path.isdir(world0_dir), f"Missing world0 dir at {world0_dir}"
    assert os.path.isdir(aria_dir), f"Missing aria dir at {aria_dir}"
    assert os.path.isfile(props_path), f"Missing shaders.properties at {props_path}"

    world0_files = sorted(os.listdir(world0_dir))
    aria_files = sorted(os.listdir(aria_dir))

    # 1. Inventory check
    assert len(world0_files) == len(aria_files), f"Count mismatch: world0 has {len(world0_files)}, aria has {len(aria_files)}"
    assert set(world0_files) == set(aria_files), f"Inventory mismatch: diff is {set(world0_files) ^ set(aria_files)}"

    modified_count = 0
    identical_count = 0

    include_pattern = re.compile(r'#include\s+["<](/?[^>"]+)[">]')

    for filename in aria_files:
        w0_path = os.path.join(world0_dir, filename)
        aria_path = os.path.join(aria_dir, filename)

        with open(w0_path, "rb") as f_w0, open(aria_path, "rb") as f_aria:
            b_w0 = f_w0.read()
            b_aria = f_aria.read()

        # Check include target existence
        for line in b_aria.decode("utf-8", errors="ignore").splitlines():
            m = include_pattern.search(line)
            if m:
                target_rel = m.group(1).lstrip("/")
                target_path = os.path.join(shaders_dir, target_rel)
                assert os.path.isfile(target_path), f"{filename} includes non-existent {target_rel}"

        if b"#define WORLD_OVERWORLD" in b_w0:
            assert b_aria.count(b"#define WORLD_OVERWORLD") == 1, f"{filename}: expected exactly one WORLD_OVERWORLD in aria"
            assert b_aria.count(b"#define WORLD_ARIA") == 1, f"{filename}: expected exactly one WORLD_ARIA in aria"

            lines_aria = b_aria.splitlines(keepends=True)
            overworld_idx = -1
            aria_idx = -1
            for i, line in enumerate(lines_aria):
                if line.strip() == b"#define WORLD_OVERWORLD":
                    overworld_idx = i
                elif line.strip() == b"#define WORLD_ARIA":
                    aria_idx = i

            assert overworld_idx >= 0, f"{filename}: WORLD_OVERWORLD not found as standalone directive"
            assert aria_idx == overworld_idx + 1, (
                f"{filename}: WORLD_ARIA must be placed immediately following WORLD_OVERWORLD "
                f"(found at line {aria_idx+1}, expected {overworld_idx+2})"
            )

            lines_without_aria = lines_aria[:aria_idx] + lines_aria[aria_idx + 1:]
            assert b"".join(lines_without_aria) == b_w0, (
                f"{filename}: has unintended alterations beyond the single immediately-following WORLD_ARIA define"
            )
            modified_count += 1
        else:
            assert b"#define WORLD_ARIA" not in b_aria, f"{filename}: unexpected WORLD_ARIA in non-overworld file"
            assert b_aria == b_w0, f"{filename}: expected byte-identical to world0"
            identical_count += 1

    print(f"Wrapper validation SUCCESS: {len(aria_files)} files checked ({modified_count} specialized, {identical_count} byte-identical). All include targets verified.")

    # 2. shaders.properties Program Toggle Parity Check
    with open(props_path, "r", encoding="utf-8") as f:
        props_lines = f.readlines()

    world0_toggles = []
    aria_toggles = []

    current_context = []
    prog_regex = re.compile(r"^(\s*)program\.(world0|aria)/([a-zA-Z0-9_]+)\.enabled\s*=\s*(.*)$")

    for line in props_lines:
        s = line.strip()
        if s.startswith("#ifdef") or s.startswith("#ifndef") or s.startswith("#if"):
            current_context.append(s)
        elif s.startswith("#else"):
            if current_context:
                current_context[-1] = f"{current_context[-1]} -> #else"
        elif s.startswith("#endif"):
            if current_context:
                current_context.pop()

        m = prog_regex.match(line)
        if m:
            indent, dim, prog_name, rhs = m.groups()
            entry = (prog_name, rhs.strip(), tuple(current_context))
            if dim == "world0":
                world0_toggles.append(entry)
            elif dim == "aria":
                aria_toggles.append(entry)

    assert len(world0_toggles) > 0, "No program.world0/... toggles found in shaders.properties"
    assert len(world0_toggles) == len(aria_toggles), (
        f"Program toggle count mismatch: world0 has {len(world0_toggles)}, aria has {len(aria_toggles)}"
    )

    world0_set = set(world0_toggles)
    aria_set = set(aria_toggles)

    missing_in_aria = world0_set - aria_set
    extra_in_aria = aria_set - world0_set

    assert not missing_in_aria, f"Missing program.aria/... toggles in shaders.properties: {missing_in_aria}"
    assert not extra_in_aria, f"Extra unexpected program.aria/... toggles in shaders.properties: {extra_in_aria}"

    for idx, (w0, ar) in enumerate(zip(world0_toggles, aria_toggles)):
        assert w0 == ar, f"Toggle order/context mismatch at index {idx}: world0={w0} vs aria={ar}"

    print(f"Property parity SUCCESS: all {len(world0_toggles)} program.world0 toggles perfectly mirrored by program.aria.")

if __name__ == "__main__":
    validate()
