import json
import sys

# Check if a filename was provided
if len(sys.argv) < 2:
    print("Usage: python validate_jsonl.py <path_to_your_file.jsonl>")
    sys.exit(1)

filepath = sys.argv[1]
print(f"Validating file: {filepath}\n")

found_errors = 0
with open(filepath, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        try:
            # Try to parse the line as JSON
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f"--- ERROR FOUND ON LINE {i+1} ---")
            print(f"Error: {e}")
            # Print the first 300 characters of the problematic line
            print(f"Problematic line (start): {line[:300]}")
            print("-" * 20)
            found_errors += 1

if found_errors == 0:
    print("Success! The entire file is valid JSONL.")
else:
    print(f"\nFinished. Found a total of {found_errors} invalid lines.")