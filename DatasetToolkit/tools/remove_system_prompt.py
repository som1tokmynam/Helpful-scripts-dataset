# tools/remove_system_prompt.py

import json
from pathlib import Path

def remove_system_prompt_from_jsonl(input_file: str, output_file: str, system_role: str):
    """
    Reads a JSONL file, removes the first conversation turn if it's a system prompt,
    and writes the result to a new JSONL file.
    
    Args:
        input_file (str): Path to the input .jsonl file.
        output_file (str): Path to the output .jsonl file.
        system_role (str): The role name to identify system messages (e.g., 'system').
    """
    if not all([input_file, output_file, system_role]):
        raise ValueError("Input file, output file, and system role must be specified.")
        
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input and output files cannot be the same.")

    print(f"Starting processing for '{input_path}'...")
    print(f"System role to remove: '{system_role}'")
    lines_processed = 0
    system_prompts_removed = 0

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for i, line in enumerate(infile, 1):
            try:
                data = json.loads(line)
                
                if 'conversations' in data and isinstance(data['conversations'], list) and data['conversations']:
                    first_message = data['conversations'][0]
                    if first_message.get('from') == system_role:
                        data['conversations'] = data['conversations'][1:]
                        system_prompts_removed += 1
                
                outfile.write(json.dumps(data) + '\n')
                lines_processed += 1
                
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON on line {i}. Skipping.")
            except Exception as e:
                print(f"An error occurred on line {i}: {e}")

    print("\nProcessing complete!")
    print(f"Total lines processed: {lines_processed}")
    print(f"System prompts removed: {system_prompts_removed}")
    print(f"New data saved to: '{output_path}'")