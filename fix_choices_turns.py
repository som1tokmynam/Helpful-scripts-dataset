import json
import os

# --- Configuration ---
# 1. Enter the name of your dataset file here
INPUT_FILENAME = 'combined_good_and_above_stories_list_sharegpt.jsonl' 

# 2. This will be the name of the new, corrected file
OUTPUT_FILENAME = 'combined_good_and_above_stories_list_sharegpt_fixed.jsonl'
# ---------------------

fixed_turns_count = 0  # Renamed to reflect we are fixing turns, not just lines
total_lines_count = 0

# Check if the input file exists before starting
if not os.path.exists(INPUT_FILENAME):
    print(f"Error: Input file not found at '{INPUT_FILENAME}'")
    print("Please make sure the script is in the same folder as your dataset and the filename is correct.")
else:
    print(f"Starting to process '{INPUT_FILENAME}'...")

    # Open the original file for reading and a new file for writing
    with open(INPUT_FILENAME, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILENAME, 'w', encoding='utf-8') as outfile:

        for line in infile:
            total_lines_count += 1
            try:
                # Load the JSON object from the current line
                data = json.loads(line)

                # --- The Corrected Logic ---
                # Check if the line has a "conversations" key which is a list
                if 'conversations' in data and isinstance(data['conversations'], list):
                    
                    # Loop through each turn dictionary inside the conversations list
                    for turn in data['conversations']:
                        
                        # Check if this turn is a candidate for fixing
                        if turn.get('from') == 'gpt' and 'value' in turn:
                            value_str = turn['value']
                            
                            # Check if the value starts with <choices> but doesn't end with </choices>
                            # We use .strip() to ignore accidental whitespace
                            starts_with_choices = value_str.strip().startswith('<choices>')
                            ends_with_choices = value_str.strip().endswith('</choices>')

                            # If it's a match, fix it by appending the closing tag
                            if starts_with_choices and not ends_with_choices:
                                # Modify the 'value' within the 'turn' dictionary
                                turn['value'] = value_str + '\n</choices>'
                                fixed_turns_count += 1
                                # Optional: uncomment to see which lines are being fixed
                                # print(f"Fixed a turn in line {total_lines_count}")

                # Write the data object (either original or modified) back to the new file
                # This correctly saves the entire conversation with the fixed turn
                outfile.write(json.dumps(data) + '\n')

            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON on line {total_lines_count}. Copying the line as-is.")
                outfile.write(line)
            except Exception as e:
                print(f"An unexpected error occurred on line {total_lines_count}: {e}. Skipping line.")

    print("\n--- Processing Complete ---")
    print(f"Total lines read: {total_lines_count}")
    print(f"Total individual GPT turns fixed: {fixed_turns_count}")
    print(f"Corrected dataset saved to: '{OUTPUT_FILENAME}'")