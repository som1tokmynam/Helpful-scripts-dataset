import json
import re
import os

# Regex pattern breakdown:
# ^                                 - Matches the beginning of the string.
#
# Outer non-capturing group (?: ... | ... ) allows EITHER of the two main patterns to match.
# This ensures we handle both multi-line standalone blocks and single-line {role}: prefixes.
pattern_to_remove = re.compile(
    r"^(?:"
    # Pattern 1: Multi-line standalone names/roles (original behavior)
    r"(?:[\s]*\{[a-zA-Z]+\}(?::)?\s*\n)?"     # Optional initial {role} line ending in \n
    # We replaced \w+ with a character set [\w\s'\"-]+ to include spaces, quotes, and hyphens.
    r"(?:[\s]*([\w\s'\"-]+)(?::)?\s*\n)+"     # One or more standalone name/role lines ending in \n
    r"|"                                      # OR
    # Pattern 2: Single-line {role} prefix (new behavior for cases like "{user}: "I'm")
    r"[\s]*\{[a-zA-Z]+\}(?::)?\s*"            # {role} tag, optional colon, and any trailing whitespace (not necessarily \n)
    r")"
)

def clean_conversation_value(text):
    """
    Applies the regex to clean the beginning of the value string.
    Returns the cleaned text and a boolean indicating if a change was made.
    """
    if not isinstance(text, str):
        return text, False # Ensure it's a string, if not, return as is

    original_text = text
    # Use sub with count=1 to ensure only the first block of consecutive matches at the beginning is replaced
    cleaned_text = pattern_to_remove.sub("", text, count=1)

    return cleaned_text, original_text != cleaned_text

def remove_standalone_names_main(input_file: str, output_file: str):
    """
    Processes a JSONL file to remove standalone names/roles from 'value' fields
    within 'conversations' arrays. Each line of the input file is treated as a
    separate JSON object.

    Args:
        input_file (str): Path to the input JSONL file.
        output_file (str): Path to the output JSONL file.
    """
    if not input_file or not output_file:
        print("Error: Input and output file paths cannot be empty.")
        return

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return

    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")

    processed_lines = 0
    modified_values = 0
    skipped_lines = 0

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            for line_num, line in enumerate(infile, 1):
                try:
                    data = json.loads(line) # Correctly parses each line as a single JSON object
                    if 'conversations' in data and isinstance(data['conversations'], list):
                        for turn in data['conversations']:
                            if 'value' in turn and isinstance(turn['value'], str):
                                cleaned_value, was_modified = clean_conversation_value(turn['value'])
                                if was_modified:
                                    turn['value'] = cleaned_value
                                    modified_values += 1
                    outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
                    processed_lines += 1
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON line {line_num} (Error: {e}): {line.strip()}")
                    skipped_lines += 1
                except Exception as e:
                    print(f"Error processing line {line_num}: {e}. Skipping line.")
                    skipped_lines += 1

        print(f"\nProcessing complete!")
        print(f"Lines processed: {processed_lines}")
        print(f"Values modified: {modified_values}")
        if skipped_lines > 0:
            print(f"Lines skipped due to errors: {skipped_lines}")

    except IOError as e:
        print(f"File I/O Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # Expanded example data to test all new cases
    sample_data = [
        # Original problem case
        {"conversations": [{"from": "gpt", "value": "Scorch:\nScorch\n*The iron gate slams shut..."}]},
        # New cases with special characters
        {"conversations": [{"from": "gpt", "value": "Valerius \"The Scourge\":\nThe plan is simple."}]},
        {"conversations": [{"from": "gpt", "value": "Brother-prophet ka'el:\nWe must act now."}]},
        {"conversations": [{"from": "gpt", "value": "Ka'el:\nIndeed."}]},
        # Multi-line case with special characters
        {"conversations": [{"from": "gpt", "value": "Brother-prophet ka'el:\nKa'el:\nThis text should remain."}]},
        # Case with a {role} tag that should be removed
        {"conversations": [{"from": "gpt", "value": "{user}:Tell me a story."}]},
        # A normal case that should not be changed
        {"conversations": [{"from": "gpt", "value": "This is a normal sentence that should not be modified."}]}
    ]

    test_input_file = "test_input_names.jsonl"
    test_output_file = "test_output_names_cleaned.jsonl"

    with open(test_input_file, 'w', encoding='utf-8') as f:
        for item in sample_data:
            f.write(json.dumps(item) + '\n')

    print(f"Created '{test_input_file}' for testing.")
    remove_standalone_names_main(test_input_file, test_output_file)
    print(f"\nOutput saved to '{test_output_file}'. You can check its contents.")
    print("-" * 20)
    print("Cleaned file content:")
    with open(test_output_file, 'r', encoding='utf-8') as f:
        print(f.read())