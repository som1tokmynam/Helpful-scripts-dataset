# tools/validate_dataset.py
import json
import sys

def validate_and_clean_jsonl(input_file, output_file):
    print(f"[*] Starting validation and cleaning of {input_file}...")
    lines_written = 0
    lines_skipped = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            for i, line in enumerate(infile, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if isinstance(data, dict) and 'text' in data and isinstance(data['text'], str):
                        outfile.write(json.dumps(data) + '\n')
                        lines_written += 1
                    else:
                        print(f"Warning: Skipping line {i} due to incorrect structure: {line}", file=sys.stderr)
                        lines_skipped += 1
                except json.JSONDecodeError:
                    print(f"Warning: Skipping line {i} due to invalid JSON format: {line}", file=sys.stderr)
                    lines_skipped += 1
    except FileNotFoundError:
        raise Exception(f"Input file not found at '{input_file}'")
        
    print("\n[+] Processing complete.")
    print(f"    Lines written: {lines_written}")
    print(f"    Lines skipped: {lines_skipped}")