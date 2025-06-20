import json
import re
import argparse
import sys

# --- Your Cleaning Logic (Preserved from your script) ---
# This part is excellent and doesn't need to change.
# It will be applied to each JSON object from each line.

# 1. The regex using lookarounds to be extremely precise.
find_pattern = r'(?<!\w)\*(\w+)\*(?!\w)'
replace_pattern = r'\1'

def clean_json_recursively(data):
    """
    Recursively walks through a JSON-like structure (dicts and lists)
    and applies regex cleaning to all string values.
    """
    if isinstance(data, dict):
        return {key: clean_json_recursively(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_json_recursively(item) for item in data]
    elif isinstance(data, str):
        return re.sub(find_pattern, replace_pattern, data)
    else:
        return data

# --- Main Script Execution (Modified for JSONL) ---

def process_jsonl_file(input_file, output_file):
    """
    Reads a JSONL file, cleans each line, and writes to a new JSONL file.
    """
    lines_processed = 0
    lines_skipped = 0
    
    print(f"[*] Starting to clean {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            # Process the file one line at a time
            for i, line in enumerate(infile, 1):
                # Skip empty or whitespace-only lines
                if not line.strip():
                    continue
                
                try:
                    # 1. Load the JSON object from the current line
                    data_object = json.loads(line)
                    
                    # 2. Apply your recursive cleaning function to this object
                    cleaned_object = clean_json_recursively(data_object)
                    
                    # 3. Write the cleaned object back as a compact JSON string, followed by a newline
                    #    ensure_ascii=False is important for non-English characters.
                    outfile.write(json.dumps(cleaned_object, ensure_ascii=False) + '\n')
                    lines_processed += 1
                    
                except json.JSONDecodeError:
                    # If a line is not valid JSON, print a warning and skip it
                    print(f"Warning: Skipping malformed JSON on line {i}. Content: {line.strip()}", file=sys.stderr)
                    lines_skipped += 1

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found. Please check the name.", file=sys.stderr)
        sys.exit(1)
        
    print("\n[+] Cleaning complete!")
    print(f"    Total lines processed successfully: {lines_processed}")
    print(f"    Total lines skipped due to errors: {lines_skipped}")
    print(f"    Cleaned data saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Cleans asterisks from string values within a JSONL file."
    )
    parser.add_argument(
        "input_file", 
        help="Path to the input JSONL file (e.g., 'my_data.jsonl')."
    )
    parser.add_argument(
        "output_file", 
        help="Path for the cleaned output JSONL file (e.g., 'my_data_cleaned.jsonl')."
    )
    
    args = parser.parse_args()
    
    process_jsonl_file(args.input_file, args.output_file)