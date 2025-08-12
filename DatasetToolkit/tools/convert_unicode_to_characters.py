import json
import argparse
import sys

def fix_mojibake(text: str) -> str:
    """
    Attempts to fix a common encoding issue where UTF-8 text was wrongly
    interpreted as a single-byte encoding (like latin-1 or cp1252).
    """
    try:
        # This is the core of the fix:
        # 1. Encode the garbled string back to bytes using the encoding it was
        #    likely misinterpreted with. 'latin-1' is a safe choice because it
        #    can represent all 256 byte values.
        # 2. Decode those bytes correctly using the intended 'utf-8' encoding.
        return text.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # If the text was not garbled, this process might fail.
        # In that case, we return the original text untouched.
        return text

def normalize_unicode_in_jsonl(input_file: str, output_file: str):
    """
    Reads a JSONL file, decodes Unicode escapes, fixes common encoding
    errors (mojibake), and writes the result to a new file.

    Args:
        input_file: The path to the input JSONL file.
        output_file: The path for the normalized output JSONL file.
    """
    print(f"[*] Starting Unicode normalization and fixing for: {input_file}")

    lines_processed = 0
    lines_skipped = 0

    try:
        # It's still best practice to open with utf-8 and error handling.
        with open(input_file, 'r', encoding='utf-8', errors='replace') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:

            for i, line in enumerate(infile, 1):
                if not line.strip():
                    continue

                try:
                    # 1. Load the JSON object from the line.
                    data_object = json.loads(line)

                    # 2. Recursively traverse the JSON to find and fix all strings.
                    def recursive_fix(obj):
                        if isinstance(obj, dict):
                            return {k: recursive_fix(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [recursive_fix(elem) for elem in obj]
                        elif isinstance(obj, str):
                            # Apply the mojibake fix to each string value.
                            return fix_mojibake(obj)
                        else:
                            return obj

                    fixed_data_object = recursive_fix(data_object)

                    # 3. Write the fixed object back to a string, ensuring that
                    #    actual Unicode characters are written, not \uXXXX escapes.
                    normalized_line = json.dumps(fixed_data_object, ensure_ascii=False)

                    outfile.write(normalized_line + '\n')
                    lines_processed += 1

                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON on line {i}. Content: {line.strip()}", file=sys.stderr)
                    lines_skipped += 1

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file}'", file=sys.stderr)
        # Re-raise the exception to be caught by the GUI's error handler.
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        # Re-raise for the GUI to display the error.
        raise

    print("\n[+] Normalization complete!")
    print(f"    - Lines processed successfully: {lines_processed}")
    print(f"    - Lines skipped due to errors: {lines_skipped}")
    print(f"    - Normalized data saved to: {output_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Reads a JSONL file, decodes Unicode escapes, fixes common encoding errors, and saves a new file."
    )
    parser.add_argument(
        'input_file',
        help='The path to the input JSONL file.'
    )
    parser.add_argument(
        'output_file',
        help='The path for the normalized output JSONL file.'
    )
    args = parser.parse_args()

    try:
        normalize_unicode_in_jsonl(args.input_file, args.output_file)
    except Exception as e:
        # The function already prints details, so just exit with an error code.
        sys.exit(1)