import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
RULES_PATH = os.path.join(os.getcwd(), "hl7apy", "v2_3", "v2_3.rules")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_rules():
    mandatory_fields = []
    print("\n📄 Loading mandatory fields from rules:")
    with open(RULES_PATH, "r") as f:
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
                field_id = idx + 1  # because MSH.2 starts at parts[1]
                val = parts[idx].strip()
                key = f"MSH.{field_id}"
                if val:
                    field_map[key] = val
                    print(f"✅ {key} = {val}")
                else:
                    print(f"⚪ {key} = [empty]")
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
            mandatory_fields = load_rules()
            # Step 1: Get all segment names from the message
            present_segments = {key.split('.')[0] for key in present_fields.keys()}

            # Step 2: Only validate rules for those segments
            # Step 2: Only validate rules for those segments
            print("\n📌 Final comparison starting...")
            print("🟨 Present segments:", present_segments)
            print("🟦 Present fields:", list(present_fields.keys()))
            print("📄 Mandatory fields from rules (filtered by present segments):")
            print([f for f in mandatory_fields if f.split('.')[0] in present_segments])

            missing = [
                field for field in mandatory_fields
                if field.split('.')[0] in present_segments and field not in present_fields
            ]

            print("❗Missing fields after comparison:", missing)

            if not missing:
                result = "✅ Validation successful. All mandatory fields are present."
            else:
                result = f"❌ Missing fields:\n" + "\n".join(missing)
        else:
            result = "❌ Please upload a .hl7 or .txt file."
    return render_template("index.html", result=result)
