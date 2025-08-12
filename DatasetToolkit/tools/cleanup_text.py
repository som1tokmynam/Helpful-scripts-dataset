import json
import sys
import re

def cleanup_text_in_jsonl(input_file: str, output_file: str):
    """
    Reads a JSONL file, cleans specific text patterns from the 'value' field
    of each turn, and removes turns that become empty after cleaning.
    """
    if not input_file or not output_file:
        print("Error: Input and Output file paths must be provided.")
        return

    # Regex to find a line that ONLY contains a speaker name (e.g., "Firestorm:")
    speaker_only_pattern = re.compile(r"^[\s\n]*[\w\s]+:[\s\n]*$", re.IGNORECASE)

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

                            # 1. Check if the turn is just a speaker name and remove it.
                            if speaker_only_pattern.match(cleaned_value):
                                made_change_this_line = True
                                continue

                            # 2. Clean up block-level dividers and specific scene markers.
                            #    This correctly handles 'Scene:' without affecting other quoted text.
                            cleaned_value = re.sub(r"(\n\s*)*(\*\*Scene:\*\*|'Scene:')\s*(\n\s*)*", '\n\n', cleaned_value, flags=re.IGNORECASE)
                            cleaned_value = re.sub(r'(\n\s*)*-- end character info --\s*(\n\s*)*', '\n\n', cleaned_value, flags=re.IGNORECASE)
                            cleaned_value = re.sub(r'(\n\s*)*-{2,}\s*(\n\s*)*', '\n\n', cleaned_value)
                            cleaned_value = re.sub(r'^\s*[\*\s]+\s*$', '', cleaned_value, flags=re.MULTILINE)

                            # 3. Remove markdown-like formatting characters.
                            #    Removes **, ***, etc., but preserves single * for italics.
                            cleaned_value = re.sub(r'\*{2,}', '', cleaned_value)

                            # --- CORRECTED LOGIC ---
                            # The overly broad rule for single quotes has been REMOVED
                            # to avoid damaging dialogue like 'Hello, how are you?'.
                            # The 'Scene:' rule above is sufficient for specific cases.
                            # --- END CORRECTION ---

                            # 4. Consolidate whitespace.
                            cleaned_value = re.sub(r'\n(\s*\n){2,}', '\n\n', cleaned_value)

                            # 5. Final cleanup.
                            cleaned_value = cleaned_value.strip()

                            if cleaned_value != original_value:
                                made_change_this_line = True

                            # 6. If cleaning made the turn empty, skip it.
                            if not cleaned_value:
                                continue

                            turn['value'] = cleaned_value

                        cleaned_conversations.append(turn)

                    if made_change_this_line:
                        lines_with_changes += 1

                    if cleaned_conversations:
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