import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from hl7apy.v2_3.message_segment_validator import get_required_segments

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_rules(version):
    rules_file = f"hl7apy/v2_3/v2_3.rules" if version == "2.3" else f"hl7apy/v{version.replace('.', '_')}/v{version.replace('.', '_')}.rules"
    if not os.path.exists(rules_file):
        print(f"❌ Rules file not found for version {version}")
        return []

    mandatory_fields = []
    print(f"\n📄 Loading mandatory fields from rules ({rules_file}):")
    with open(rules_file, "r") as f:
        for line in f:
            if "must be not empty" in line:
                field = line.split('"')[1]
                mandatory_fields.append(field)
                print(f"🔹 {field}")
    return mandatory_fields


def parse_hl7_fields(message_lines):
    field_map = {}
    print("\n🟦 Parsed HL7 fields:")
    for line in message_lines:
        if not line.strip() or '|' not in line:
            continue
        parts = line.strip().split('|')
        segment = parts[0]
        if segment == "MSH":
            # MSH.1 is the field separator, not captured in split
            field_map["MSH.1"] = "|"
            print("✅ MSH.1 = |")
            for idx in range(1, len(parts)):
                field_id = idx + 1
                val = parts[idx].strip()
                key = f"{segment}.{field_id}"
                if val:
                    field_map[key] = val
                    print(f"✅ {key} = {val}")
                else:
                    print(f"⚪ {key} = [empty]")
                if field_id == 9 and "^" in val:
                    msg_type_code = val.split("^")[0]
                    trigger_event = val.split("^")[1]
                    field_map["MESSAGE_TYPE"] = f"{msg_type_code}_{trigger_event}"
                elif field_id == 12:
                    field_map["VERSION"] = val
        else:
            for idx in range(1, len(parts)):
                key = f"{segment}.{idx}"
                val = parts[idx].strip()
                if val:
                    field_map[key] = val
                    print(f"✅ {key} = {val}")
                else:
                    print(f"⚪ {key} = [empty]")
    return field_map


@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        uploaded_file = request.files["hl7file"]
        if uploaded_file.filename.endswith((".hl7", ".txt")):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uploaded_file.filename))
            uploaded_file.save(file_path)

            with open(file_path, "r") as f:
                message_lines = f.readlines()

            present_fields = parse_hl7_fields(message_lines)

            present_segments = {key.split('.')[0] for key in present_fields.keys()}
            message_type = present_fields.get("MESSAGE_TYPE")
            version = present_fields.get("VERSION")

            if not version:
                result = "❌ HL7 version (MSH.12) not found. Cannot validate using versioned rules."
                return render_template("index.html", result=result)
            mandatory_fields = load_rules(version)

            # Step 1: Segment Validation based on message type
            from hl7apy.v2_3.message_segment_validator import get_required_segments
            segment_errors = []
            if message_type:
                required_segments = get_required_segments(message_type)
                for seg in required_segments:
                    if seg not in present_segments:
                        segment_errors.append(seg)

            if segment_errors:
                result = f"❌ Missing required segments for message type {message_type}: " + ", ".join(segment_errors)
                return render_template("index.html", result=result)

            # Step 2: Field Validation based on rules
            # Only validate fields belonging to segments required for this message type
            if message_type:
                required_segments = get_required_segments(message_type)
                missing = [
                    field for field in mandatory_fields
                    if field.split('.')[0] in required_segments and field not in present_fields
                ]
            else:
                # fallback: validate fields of all present segments
                missing = [
                    field for field in mandatory_fields
                    if field.split('.')[0] in present_segments and field not in present_fields
                ]

            if not missing:
                result = "✅ Validation successful. All mandatory fields are present."
            else:
                result = f"❌ Missing fields:\n" + "\n".join(missing)
        else:
            result = "❌ Please upload a .hl7 or .txt file."
    return render_template("index.html", result=result)