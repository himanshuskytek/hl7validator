# import os
# from hl7apy.v2_3 import messages, groups, segments
#
# COMBINED_RULES_FILE = "hl7apy/v2_3/v2_3.combined_using_groups.rules"
#
# def is_required(repetition):
#     return repetition[0] == 1
#
# def collect_segments_from_group(group_name, visited_groups=None):
#     visited_groups = visited_groups or set()
#     if group_name in visited_groups:
#         return set()
#     visited_groups.add(group_name)
#
#     segs = set()
#     group_def = groups.GROUPS.get(group_name)
#     if not group_def:
#         print(f"⚠️ Group not found: {group_name}")
#         return segs
#
#     for entry in group_def[1]:
#         name, _, rep, type_ = entry
#         if type_ == 'SEG' and is_required(rep):
#             segs.add(name)
#         elif type_ == 'GRP' and is_required(rep):
#             segs.update(collect_segments_from_group(name, visited_groups))
#     return segs
#
# def generate_combined_rules():
#     os.makedirs(os.path.dirname(COMBINED_RULES_FILE), exist_ok=True)
#
#     total_written = 0
#     with open(COMBINED_RULES_FILE, "w") as f:
#         for msg_type, msg_def in messages.MESSAGES.items():
#             print(f"\n📨 Processing message: {msg_type}")
#             required_segments = set()
#             for entry in msg_def[1]:
#                 name, _, rep, type_ = entry
#                 if type_ == 'SEG' and is_required(rep):
#                     print(f"  🔹 Required SEG: {name}")
#                     required_segments.add(name)
#                 elif type_ == 'GRP' and is_required(rep):
#                     print(f"  🔸 Required GRP: {name}")
#                     segs = collect_segments_from_group(name)
#                     required_segments.update(segs)
#                     print(f"    → Segments from group: {segs}")
#
#             for seg in sorted(required_segments):
#                 f.write(f'SEGMENT_REQUIRED "{msg_type}" "{seg}"\n')
#                 total_written += 1
#
#             for seg in required_segments:
#                 if seg in segments.SEGMENTS:
#                     fields = segments.SEGMENTS[seg][1]
#                     for i, field_def in enumerate(fields):
#                         if field_def and len(field_def) >= 3 and is_required(field_def[2]):
#                             f.write(f'FIELD_REQUIRED "{msg_type}" "{seg}.{i+1}"\n')
#                             total_written += 1
#
#     print(f"\n✅ Finished. Total rules written: {total_written}")
#     print(f"📄 Output file: {COMBINED_RULES_FILE}")
#
# if __name__ == "__main__":
#     generate_combined_rules()










import os
from hl7apy.v2_3 import messages, groups, segments

# ✔ Save file to this nested path
COMBINED_RULES_FILE = "v2_3.combined.rules"

def is_required(rep):
    return rep[0] == 1

def collect_required_segments_from_group(group_name, visited=None):
    if visited is None:
        visited = set()
    if group_name in visited:
        return set()
    visited.add(group_name)

    required_segments = set()
    group_def = groups.GROUPS.get(group_name)
    if not group_def:
        return required_segments

    for entry in group_def[1]:
        name, _, rep, kind = entry
        if kind == 'SEG' and is_required(rep):
            required_segments.add(name)
        elif kind == 'GRP':
            # ✅ Explore any sub-group, even if it's optional, in case it contains required segments
            required_segments.update(collect_required_segments_from_group(name, visited))

    return required_segments


def generate_combined_rules():
    os.makedirs(os.path.dirname(COMBINED_RULES_FILE), exist_ok=True)

    total_written = 0
    with open(COMBINED_RULES_FILE, 'w') as f:
        for msg_type, msg_def in messages.MESSAGES.items():
            required_segments = set()
            for entry in msg_def[1]:
                name, _, rep, kind = entry
                if kind == 'SEG' and is_required(rep):
                    required_segments.add(name)
                elif kind == 'GRP' and is_required(rep):
                    required_segments.update(collect_required_segments_from_group(name))

            for seg in sorted(required_segments):
                f.write(f'SEGMENT_REQUIRED "{msg_type}" "{seg}"\n')
                total_written += 1

            for seg in required_segments:
                seg_def = segments.SEGMENTS.get(seg)
                if not seg_def:
                    continue
                for i, field in enumerate(seg_def[1], 1):
                    if field and is_required(field[2]):
                        f.write(f'FIELD_REQUIRED "{msg_type}" "{seg}.{i}"\n')
                        total_written += 1

    print(f"✅ Generated {total_written} rules at {COMBINED_RULES_FILE}")

if __name__ == "__main__":
    generate_combined_rules()
