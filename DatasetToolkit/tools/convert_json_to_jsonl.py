# tools/convert_json_to_jsonl.py
import json
import sys

def convert_json_to_jsonl(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f_in:
            data = json.load(f_in)
        with open(output_path, 'w', encoding='utf-8') as f_out:
            if isinstance(data, list):
                total_objects = len(data)
                print(f"Input is a list containing {total_objects} objects.")
                for obj in data:
                    json_record = json.dumps(obj, ensure_ascii=False)
                    f_out.write(json_record + '\n')
                print(f"Successfully converted {total_objects} objects.")
            elif isinstance(data, dict):
                print("Input is a single JSON object.")
                json_record = json.dumps(data, ensure_ascii=False)
                f_out.write(json_record + '\n')
                print("Successfully converted 1 object.")
            else:
                raise Exception(f"Unsupported JSON structure in {input_path}. Only a list or a single object is supported.")
    except FileNotFoundError:
        raise Exception(f"Input file not found at '{input_path}'")
    except json.JSONDecodeError:
        raise Exception(f"Failed to decode JSON from '{input_path}'. Please ensure it is a valid JSON file.")
    except Exception as e:
        raise e
    print(f"\nConversion complete. Output saved to '{output_path}'")