import json
import os
import sys

def fix_choices_tags_in_jsonl(input_file, output_file):
    """
    Scans a JSONL file and fixes GPT turns where a '<choices>' tag is opened
    but not closed by appending '\n</choices>'.
    This is intended to be called as part of a larger processing pipeline.
    """
    fixed_turns_count = 0
    total_lines_count = 0

    if not os.path.exists(input_file):
        print(f"Error: Input file not found at '{input_file}'", file=sys.stderr)
        raise FileNotFoundError(f"Input file not found at '{input_file}'")

    print(f"Starting to process '{os.path.basename(input_file)}' for unclosed <choices> tags...")

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:

        for line in infile:
            total_lines_count += 1
            try:
                data = json.loads(line)
                if 'conversations' in data and isinstance(data['conversations'], list):
                    for turn in data['conversations']:
                        if turn.get('from') == 'gpt' and 'value' in turn:
                            value_str = turn['value']
                            starts_with_choices = value_str.strip().startswith('<choices>')
                            ends_with_choices = value_str.strip().endswith('</choices>')

                            if starts_with_choices and not ends_with_choices:
                                turn['value'] = value_str + '\n</choices>'
                                fixed_turns_count += 1

                outfile.write(json.dumps(data) + '\n')

            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON on line {total_lines_count}. Copying as-is.", file=sys.stderr)
                outfile.write(line)
            except Exception as e:
                print(f"An unexpected error occurred on line {total_lines_count}: {e}. Skipping.", file=sys.stderr)

    print(f"Total lines read: {total_lines_count}")
    print(f"Total individual GPT turns with unclosed <choices> fixed: {fixed_turns_count}")