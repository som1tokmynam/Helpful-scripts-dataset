import json
import re
import os

# Regex to find standalone names/roles at the beginning of a string.
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
    Returns the cleaned text.
    """
    if not isinstance(text, str):
        return text

    cleaned_text = pattern_to_remove.sub("", text, count=1)
    return cleaned_text

def remove_standalone_names_main(input_file: str, output_file: str):
    """
    Processes a JSONL file to remove standalone names/roles from 'value' fields.
    If cleaning a value results in an empty string, the entire turn is removed.
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
    modified_lines = 0
    skipped_lines = 0

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            for line_num, line in enumerate(infile, 1):
                try:
                    data = json.loads(line)
                    
                    if 'conversations' in data and isinstance(data['conversations'], list):
                        cleaned_conversations = []
                        original_turn_count = len(data['conversations'])

                        for turn in data['conversations']:
                            if 'value' in turn and isinstance(turn['value'], str):
                                cleaned_value = clean_conversation_value(turn['value'])
                                
                                # Only keep the turn if the value is not empty after cleaning.
                                # This is the critical fix.
                                if cleaned_value.strip():
                                    turn['value'] = cleaned_value
                                    cleaned_conversations.append(turn)
                            else:
                                cleaned_conversations.append(turn)

                        if len(cleaned_conversations) != original_turn_count:
                            modified_lines += 1

                        data['conversations'] = cleaned_conversations

                    outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
                    processed_lines += 1
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON line {line_num}: {e}")
                    skipped_lines += 1

        print(f"\nProcessing complete!")
        print(f"Lines processed: {processed_lines}")
        print(f"Lines modified (had turns removed): {modified_lines}")
        if skipped_lines > 0:
            print(f"Lines skipped due to errors: {skipped_lines}")

    except IOError as e:
        print(f"File I/O Error: {e}")