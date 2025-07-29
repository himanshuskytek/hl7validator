import ast
import os

# 📌 Adjust paths to match your structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEGMENTS_PATH = os.path.join(BASE_DIR, "segments.py")
OUTPUT_RULES_PATH = os.path.join(BASE_DIR, "v2_3.rules")

def extract_rules(segment_ast):
    rules = []
    for node in ast.walk(segment_ast):
        if isinstance(node, ast.Assign):
            if isinstance(node.targets[0], ast.Name) and node.targets[0].id == "SEGMENTS":
                if isinstance(node.value, ast.Dict):
                    for key, val in zip(node.value.keys, node.value.values):
                        if not isinstance(key, ast.Constant):
                            continue
                        segment = key.value
                        if isinstance(val, ast.Tuple) and len(val.elts) >= 2:
                            fields_tuple = val.elts[1]
                            if isinstance(fields_tuple, ast.Tuple):
                                for field in fields_tuple.elts:
                                    if isinstance(field, ast.Tuple) and len(field.elts) >= 3:
                                        field_name_node = field.elts[0]
                                        repeat_range_node = field.elts[2]

                                        if not (
                                            isinstance(field_name_node, ast.Constant) and
                                            isinstance(repeat_range_node, ast.Tuple)
                                        ):
                                            continue

                                        field_name = field_name_node.value
                                        parts = field_name.split('_')
                                        if len(parts) != 2:
                                            continue  # Skip malformed field names

                                        field_id = parts[1]
                                        field_selector = f'"{segment}.{field_id}"'

                                        min_val_node = repeat_range_node.elts[0]
                                        min_val = (
                                            min_val_node.value
                                            if isinstance(min_val_node, ast.Constant)
                                            else None
                                        )

                                        if min_val == 1:
                                            rules.append(f'{field_selector} must be not empty')
                                        else:
                                            rules.append(f'{field_selector} may be empty')
    return rules

def generate_rules():
    with open(SEGMENTS_PATH, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=SEGMENTS_PATH)

    rules = extract_rules(tree)

    with open(OUTPUT_RULES_PATH, "w", encoding="utf-8") as out:
        out.write("// Auto-generated rules from segments.py\n")
        for rule in sorted(rules):
            out.write(rule + "\n")

    print(f"✅ Rules file generated at: {OUTPUT_RULES_PATH}")

if __name__ == "__main__":
    generate_rules()
