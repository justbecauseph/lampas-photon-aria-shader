import os
import sys

def validate():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    shaders_dir = os.path.join(repo_root, 'shaders')
    world0_dir = os.path.join(shaders_dir, 'world0')
    aria_dir = os.path.join(shaders_dir, 'aria')

    assert os.path.isdir(world0_dir), f'Missing world0 dir at {world0_dir}'
    assert os.path.isdir(aria_dir), f'Missing aria dir at {aria_dir}'

    world0_files = sorted(os.listdir(world0_dir))
    aria_files = sorted(os.listdir(aria_dir))

    # 1. Inventory check
    assert len(world0_files) == len(aria_files), f'Count mismatch: world0 has {len(world0_files)}, aria has {len(aria_files)}'
    assert set(world0_files) == set(aria_files), f'Inventory mismatch: diff is {set(world0_files) ^ set(aria_files)}'

    modified_count = 0
    identical_count = 0

    for filename in aria_files:
        w0_path = os.path.join(world0_dir, filename)
        aria_path = os.path.join(aria_dir, filename)

        with open(w0_path, 'rb') as f_w0, open(aria_path, 'rb') as f_aria:
            b_w0 = f_w0.read()
            b_aria = f_aria.read()

        if b'#define WORLD_OVERWORLD' in b_w0:
            assert b'#define WORLD_OVERWORLD' in b_aria, f'{filename}: missing WORLD_OVERWORLD in aria'
            assert b'#define WORLD_ARIA' in b_aria, f'{filename}: missing WORLD_ARIA in aria'

            # Assert removing '#define WORLD_ARIA\n' leaves exactly the original world0 file
            reverted = b_aria.replace(b'#define WORLD_ARIA\n', b'').replace(b'#define WORLD_ARIA\r\n', b'')
            assert reverted == b_w0, f'{filename}: has unintended alterations beyond WORLD_ARIA define'
            modified_count += 1
        else:
            assert b_aria == b_w0, f'{filename}: expected byte-identical to world0'
            identical_count += 1

    print(f'Validation SUCCESS: {len(aria_files)} files checked ({modified_count} specialized with WORLD_ARIA, {identical_count} byte-identical).')

if __name__ == '__main__':
    validate()
