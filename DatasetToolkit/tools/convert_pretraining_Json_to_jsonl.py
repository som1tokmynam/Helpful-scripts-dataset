import json

def extract_innermost_text(data_object):
    """
    Recursively navigates through nested dictionaries with the key 'text'
    to find the final string value.
    """
    current_item = data_object
    while isinstance(current_item, dict) and 'text' in current_item:
        current_item = current_item['text']
    
    if isinstance(current_item, str):
        return current_item
    else:
        return None

def convert_pretraining_json_to_jsonl(input_file, output_file):
    """
    Reads a nested JSON file, extracts the innermost 'text' value, and
    writes it to a simple JSONL file.
    """
    print(f"[*] Starting conversion from {input_file} to {output_file}...")
    lines_written = 0
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            try:
                data = json.load(infile)
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON in {input_file}. Please check the file format.")

            if not isinstance(data, list):
                print("Warning: Input file is not a JSON array. Processing it as a single item list.")
                data = [data]

            for item in data:
                text_content = extract_innermost_text(item)
                if text_content:
                    output_record = {"text": text_content}
                    outfile.write(json.dumps(output_record, ensure_ascii=False) + '\n')
                    lines_written += 1

    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found at '{input_file}'")
        
    print(f"[+] Conversion complete. Wrote {lines_written} lines to {output_file}.")