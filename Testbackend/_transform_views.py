"""Transform views: remove (data, error) destructuring + Chinese substring status mapping.

After service methods raise exceptions instead of returning (data, error) tuples:
- Remove `data, error = method(...)` → `data = method(...)`
- Remove `if error: code = 404 if '不存在' ...` blocks
- Remove `success, error = method(...)` → `success = method(...)`
- Keep the success return paths intact
"""
import re

# Known variable pairs that are destructured from service calls
PAIRS = [
    ('project_data', 'error'),
    ('project', 'error'),
    ('results', 'error'),
    ('success', 'error'),
    ('is_favorite', 'error'),
    ('result', 'error'),
    ('members_data', 'error'),
    ('member_data', 'error'),
    ('updated_count', 'error'),
]


def process(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    i = 0
    skip_until_endif = 0
    changes = 0

    while i < len(lines):
        line = lines[i]

        # Detect destructuring assignment with 'error' as second var
        # Pattern:         data_var, error = Service.method(...)
        # or:              data_var, error = method(
        stripped = line.strip()
        matched = False
        for var, err in PAIRS:
            if stripped.startswith(f'{var}, {err} =') or \
               re.match(rf'^\s*{var}\s*,\s*{err}\s*=\s*', line):
                # This line destructures into (var, error). Remove ', error'
                line = re.sub(rf'\b{var}\s*,\s*{err}\b\s*=', f'{var} =', line, count=1)
                changes += 1

                # Now scan ahead for the `if error:` block on subsequent lines
                j = i + 1
                if_block_found = False
                while j < len(lines):
                    nxt = lines[j].strip()
                    if nxt.startswith('if error:') or nxt.startswith('if not success:'):
                        # Find the end of the if block (same or lower indentation)
                        base_indent = len(lines[j]) - len(lines[j].lstrip())
                        j += 1
                        while j < len(lines):
                            nxt_stripped = lines[j].rstrip('\n')
                            # empty lines inside block are ok
                            if nxt_stripped.strip() == '':
                                j += 1
                                continue
                            cur_indent = len(nxt_stripped) - len(nxt_stripped.lstrip())
                            if cur_indent <= base_indent and not nxt_stripped.strip().startswith('#'):
                                break
                            j += 1
                        if_block_found = True
                        break
                    elif nxt.startswith('if error') or nxt.startswith('if not success'):
                        # multi-line condition
                        j += 1
                        continue
                    else:
                        break

                if if_block_found:
                    out.append(line)
                    i = j  # skip the if block entirely
                    break
                else:
                    break

            # Also handle return value, error destructuring
            if f', {err} =' in stripped:
                for v2, e2 in PAIRS:
                    if v2 != var and f'{v2}, {e2} =' in stripped:
                        continue
                break

        if not matched:
            out.append(line)
            i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(out)
    print(f'{filepath}: {changes} destructuring + error blocks removed.')


if __name__ == '__main__':
    import sys
    for f in sys.argv[1:]:
        process(f)
