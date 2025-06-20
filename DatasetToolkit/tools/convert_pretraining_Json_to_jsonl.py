import json
import argparse
import sys

def extract_innermost_text(data_object):
    """
    Recursively navigates through nested dictionaries with the key 'text'
    to find the final string value.
    """
    current_item = data_object
    while isinstance(current_item, dict) and 'text' in current_item:
        current_item = current_item['text']
    
    # After the loop, the item should be the final text string.
    # We'll return it only if it's a string, otherwise we ignore it.
    if isinstance(current_item, str):
        return current_item
    else:
        # This handles cases where the structure is malformed or ends unexpectedly.
        return None

def main():
    """
    Main function to parse arguments and run the conversion process.
    """
    parser = argparse.ArgumentParser(
        description="Convert a pretraining dataset from nested JSON to JSONL format."
    )
    parser.add_argument(
        "input_file", 
        help="Path to the input JSON file (containing a list of nested objects)."
    )
    parser.add_argument(
        "output_file", 
        help="Path for the output JSONL file."
    )
    
    args = parser.parse_args()

    print(f"[*] Starting conversion from {args.input_file} to {args.output_file}...")

    lines_written = 0
    try:
        with open(args.input_file, 'r', encoding='utf-8') as infile, \
             open(args.output_file, 'w', encoding='utf-8') as outfile:
            
            # Load the entire JSON file. Assumes it's a list of objects.
            # e.g., [ {"text": ...}, {"text": ...} ]
            try:
                data = json.load(infile)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in {args.input_file}. Please check the file format.", file=sys.stderr)
                sys.exit(1)

            # Ensure the loaded data is a list
            if not isinstance(data, list):
                print("Warning: Input file is not a JSON array. Processing it as a single item list.", file=sys.stderr)
                data = [data]

            # Process each item in the list
            for item in data:
                # Extract the deeply nested text
                text_content = extract_innermost_text(item)

                if text_content:
                    # Create the simple JSON object for the JSONL line
                    output_record = {"text": text_content}
                    
                    # Write the JSON string to the output file, followed by a newline
                    outfile.write(json.dumps(output_record) + '\n')
                    lines_written += 1

    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_file}'", file=sys.stderr)
        raise Exception("Error message")
        
    print(f"[+] Conversion complete. Wrote {lines_written} lines to {args.output_file}.")
