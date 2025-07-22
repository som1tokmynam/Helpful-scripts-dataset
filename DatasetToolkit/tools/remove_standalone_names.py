import json
import re
import os

# Regex pattern breakdown:
# ^(...|...) - Match either Pattern A or Pattern B at the start of the string.
#
# Pattern A: Multi-line block remover (greedy).
# (?: ... )+  - Matches one or more "removable lines".
#   [\s]* - Leading whitespace on the line.
#   (?: ... | ...) - The line content can be EITHER a {role} tag OR a standalone name.
#     \{[a-zA-Z]+\} - A {role} tag, e.g., {user}, {narrator}. This is checked first as it's more specific.
#     | - OR
#     [\w\s'\"-]+ - A standalone name, e.g., "The King", "NPC-1". The character set avoids matching '{' to prevent ambiguity.
#   (?::)? - An optional colon after the role/name.
#   \s*\n - Any whitespace and a mandatory newline, signifying the end of the line.
#
# Pattern B: Single-line {role} prefix remover.
#   [\s]*\{[a-zA-Z]+\}(?::)?\s*
#   This is the fallback for cases like "{user}: Hello" where there's no newline.
#   It's placed second because the multi-line pattern is more comprehensive and should be tried first.
pattern_to_remove = re.compile(
    r"^(?:"
    # Pattern A: One or more "removable lines" (standalone names or roles ending in a newline)
    r"(?:[\s]*(?:\{[a-zA-Z]+\}|[\w\s'\"-]+)(?::)?\s*\n)+"
    r"|"
    # Pattern B: A single {role} prefix, not necessarily ending in a newline
    r"[\s]*\{[a-zA-Z]+\}(?::)?\s*"
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