import json
import sys

# --- Configuration ---
# Your original file with the system prompts
input_file_path = 'D:/axolotl_training/WOF_QA_V2_simplified_data_no_rag.jsonl'
# The new file we will create, without system prompts
output_file_path = 'D:/axolotl_training/WOF_QA_V2_PROCESSED.jsonl' 
# The role name of your system messages (e.g., "system", "System", etc.)
system_role_name = 'system' 
# --- End Configuration ---

print(f"Starting processing for '{input_file_path}'...")
lines_processed = 0
system_prompts_removed = 0

with open(input_file_path, 'r', encoding='utf-8') as infile, \
     open(output_file_path, 'w', encoding='utf-8') as outfile:
    
    for line in infile:
        try:
            # Load the JSON data from one line of the file
            data = json.loads(line)
            
            # Check if the 'conversations' key exists and is a list
            if 'conversations' in data and isinstance(data['conversations'], list) and data['conversations']:
                
                # Check if the first message is a system prompt
                first_message = data['conversations'][0]
                if 'from' in first_message and first_message['from'] == system_role_name:
                    # If it is, remove it from the list
                    data['conversations'] = data['conversations'][1:]
                    system_prompts_removed += 1
            
            # Write the (potentially modified) data to the new file
            outfile.write(json.dumps(data) + '\n')
            lines_processed += 1
            
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON on a line in {input_file_path}. Skipping.")
        except Exception as e:
            print(f"An error occurred: {e}")

print("\nProcessing complete!")
print(f"Total lines processed: {lines_processed}")
print(f"System prompts removed: {system_prompts_removed}")
print(f"New data saved to: '{output_file_path}'")