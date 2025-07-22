import json
import sys
import re

def cleanup_text_in_jsonl(input_file: str, output_file: str):
    """
    Reads a JSONL file, cleans specific text patterns from the 'value' field
    of each turn in the 'conversations' list, and writes to a new file.

    Patterns removed:
    - Scene markers like '**Scene:**' or ''Scene:'' (with surrounding whitespace).
    - Standalone '---' separators (with surrounding whitespace).
    - Double asterisks '**'.
    - The phrase '-- end character info --'.
    """
    if not input_file or not output_file:
        print("Error: Input and Output file paths must be provided.")
        return

    total_lines_read, lines_with_changes = 0, 0

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:

            for i, line in enumerate(infile):
                total_lines_read += 1
                line_num = i + 1
                made_change_this_line = False

                try:
                    data = json.loads(line)
                    if 'conversations' not in data or not isinstance(data.get('conversations'), list):
                        outfile.write(line)
                        continue

                    cleaned_conversations = []
                    for turn in data['conversations']:
                        if 'value' in turn and isinstance(turn['value'], str):
                            original_value = turn['value']
                            cleaned_value = original_value

                            # --- THIS IS THE CORRECTED LOGIC ---
                            # Replace separator blocks with a double newline for a clean paragraph break.
                            # We use re.IGNORECASE for robustness against "scene:", "SCENE:", etc.
                            # The | (OR) operator in the regex handles multiple scene marker formats.
                            # Asterisks need to be escaped with a backslash.
                            cleaned_value = re.sub(r"(\n\s*)*(\*\*Scene:\*\*|'Scene:')\s*(\n\s*)*", '\n\n', cleaned_value, flags=re.IGNORECASE)
                            cleaned_value = re.sub(r'(\n\s*)*-- end character info --\s*(\n\s*)*', '\n\n', cleaned_value, flags=re.IGNORECASE)
                            cleaned_value = re.sub(r'(\n\s*)*---\s*(\n\s*)*', '\n\n', cleaned_value)

                            # Remove double asterisks (for emphasis, etc.)
                            cleaned_value = cleaned_value.replace('**', '')

                            # Final strip removes any leading/trailing whitespace or newlines,
                            # which perfectly handles cases where separators were at the start/end of the text.
                            cleaned_value = cleaned_value.strip()

                            if cleaned_value != original_value:
                                made_change_this_line = True

                            turn['value'] = cleaned_value

                        cleaned_conversations.append(turn)

                    if made_change_this_line:
                        lines_with_changes += 1

                    data['conversations'] = cleaned_conversations
                    outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

                except json.JSONDecodeError:
                    print(f"Warning: Line {line_num} is not valid JSON. Copying as-is.")
                    outfile.write(line)

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file}'")
        sys.exit(1)

    print("\n--- Text Cleanup Complete ---")
    print(f"Total lines read: {total_lines_read}")
    print(f"Lines with changes: {lines_with_changes}")
    print(f"Cleaned data written to: '{output_file}'")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python cleanup_text.py <input_file.jsonl> <output_file.jsonl>")
    else:
        cleanup_text_in_jsonl(sys.argv[1], sys.argv[2])