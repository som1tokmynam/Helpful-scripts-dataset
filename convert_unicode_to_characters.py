import json
import argparse
import sys

def normalize_unicode_in_jsonl(input_file, output_file):
    """
    Reads a JSONL file, decodes all Unicode escape sequences into their
    actual characters, and writes the result to a new file.

    Args:
        input_file (str): The path to the input JSONL file.
        output_file (str): The path for the normalized output JSONL file.
    """
    print(f"[*] Starting Unicode normalization for: {input_file}")
    
    lines_processed = 0
    lines_skipped = 0

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for i, line in enumerate(infile, 1):
                # Skip empty lines
                if not line.strip():
                    continue
                
                try:
                    # 1. Load the JSON object. Python automatically handles \uXXXX escapes.
                    #    For example, a string containing "\u201c" becomes a Python
                    #    string containing the actual “ character.
                    data_object = json.loads(line)
                    
                    # 2. Write the object back to a string, but with ensure_ascii=False.
                    #    This tells json.dumps() to write the actual “ character
                    #    instead of converting it back to "\u201c".
                    normalized_line = json.dumps(data_object, ensure_ascii=False)
                    
                    # 3. Write the new line to the output file.
                    outfile.write(normalized_line + '\n')
                    lines_processed += 1
                    
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON on line {i}. Content: {line.strip()}", file=sys.stderr)
                    lines_skipped += 1

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n[+] Normalization complete!")
    print(f"    - Lines processed successfully: {lines_processed}")
    print(f"    - Lines skipped due to errors: {lines_skipped}")
    print(f"    - Normalized data saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Reads a JSONL file and normalizes Unicode escape sequences (e.g., \\u201c) into their actual characters (e.g., “).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input_file",
        help="The path to the input JSONL file containing Unicode escapes."
    )
    parser.add_argument(
        "output_file",
        help="The path for the cleaned output JSONL file with actual Unicode characters."
    )

    args = parser.parse_args()
    
    normalize_unicode_in_jsonl(args.input_file, args.output_file)