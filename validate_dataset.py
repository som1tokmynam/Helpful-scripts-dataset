import json
import argparse
import sys

def main():
    """
    Reads a file line-by-line, validates that each line is a correct JSON
    object with the format {"text": "..."}, and writes valid lines to an output file.
    """
    parser = argparse.ArgumentParser(
        description="Validates and cleans a JSONL file to ensure proper format."
    )
    parser.add_argument(
        "input_file", 
        help="Path to the input file (expected to be in JSONL format)."
    )
    parser.add_argument(
        "output_file", 
        help="Path for the cleaned and validated output JSONL file."
    )
    
    args = parser.parse_args()

    print(f"[*] Starting validation and cleaning of {args.input_file}...")

    lines_written = 0
    lines_skipped = 0
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as infile, \
             open(args.output_file, 'w', encoding='utf-8') as outfile:
            
            # Process the file one line at a time
            for i, line in enumerate(infile, 1):
                # Remove leading/trailing whitespace which can cause issues
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                try:
                    # Try to parse the line as JSON
                    data = json.loads(line)
                    
                    # --- The Validation Logic ---
                    # 1. Is it a dictionary?
                    # 2. Does it have the 'text' key?
                    # 3. Is the value for 'text' a string?
                    if isinstance(data, dict) and 'text' in data and isinstance(data['text'], str):
                        # If valid, write it to the output file
                        # json.dumps ensures it's perfectly formatted standard JSON
                        outfile.write(json.dumps(data) + '\n')
                        lines_written += 1
                    else:
                        # The JSON is valid, but the structure is wrong
                        print(f"Warning: Skipping line {i} due to incorrect structure: {line}", file=sys.stderr)
                        lines_skipped += 1

                except json.JSONDecodeError:
                    # The line is not valid JSON
                    print(f"Warning: Skipping line {i} due to invalid JSON format: {line}", file=sys.stderr)
                    lines_skipped += 1

    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_file}'", file=sys.stderr)
        sys.exit(1)
        
    print("\n[+] Processing complete.")
    print(f"    Lines written: {lines_written}")
    print(f"    Lines skipped: {lines_skipped}")

if __name__ == "__main__":
    main()