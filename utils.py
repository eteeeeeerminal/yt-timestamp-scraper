import json

def aligned_json_dump(obj, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4, separators=(',', ': '))

