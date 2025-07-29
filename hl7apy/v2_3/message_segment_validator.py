# hl7apy/v2_3/message_segment_validator.py

import ast

MESSAGES_PATH = "hl7apy/v2_3/messages.py"

def get_required_segments(message_type):
    with open(MESSAGES_PATH, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=MESSAGES_PATH)

    required = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.targets[0], ast.Name) and node.targets[0].id == "MESSAGES":
                messages_dict = node.value
                for key, val in zip(messages_dict.keys, messages_dict.values):
                    if not isinstance(key, ast.Constant): continue
                    if key.value == message_type:
                        if isinstance(val, ast.Tuple):
                            sequence = val.elts[1]
                            if isinstance(sequence, ast.Tuple):
                                for item in sequence.elts:
                                    if isinstance(item, ast.Tuple) and len(item.elts) >= 3:
                                        seg_name = item.elts[0].value
                                        rep = item.elts[2]
                                        if isinstance(rep, ast.Tuple):
                                            min_val = rep.elts[0].value
                                            if min_val == 1:
                                                required.append(seg_name)
                        return required
    return []
