import json
from pathlib import Path

# --- Configuration (used for standalone execution) ---
# 1. Set the path to your original dataset file
_input_file_path_standalone = Path("D:/axolotl_training/combined_incredible_stories_list_sharegpt.jsonl")

# 2. Set the desired name for the new, corrected file
_output_file_path_standalone = Path("D:/axolotl_training/combined_incredible_stories_list_sharegpt_CORRECTED.jsonl")

# 3. Set the role key for the assistant (based on your YAML)
ASSISTANT_ROLE = "gpt"
# --- End Configuration ---


def process_conversation(conversation_list):
    """
    Iterates through a conversation and merges consecutive turns
    from the assistant.
    """
    if not conversation_list:
        return [], 0

    corrected_list = []
    merges_done = 0
    
    # Start with the first turn
    if conversation_list:
        corrected_list.append(conversation_list[0])

    for i in range(1, len(conversation_list)):
        current_turn = conversation_list[i]
        last_turn_in_corrected = corrected_list[-1]

        # Check if the last turn and the current turn are both from the assistant
        if (last_turn_in_corrected.get("from") == ASSISTANT_ROLE and
                current_turn.get("from") == ASSISTANT_ROLE):
            
            # Merge the 'value' fields
            last_turn_in_corrected["value"] += f"\n\n{current_turn['value']}"
            merges_done += 1
        else:
            # If no merge is needed, just append the current turn
            corrected_list.append(current_turn)
            
    return corrected_list, merges_done


def fix_consecutive_turns(input_file, output_file):
    """
    Main function to read, process, and write the dataset.
    This is the function called by the GUI toolkit.
    """
    input_file_path = Path(input_file)
    output_file_path = Path(output_file)
    
    print(f"Starting dataset correction...")
    print(f"Input file: {input_file_path}")
    print(f"Output file: {output_file_path}")

    if not input_file_path.exists():
        # Raise an error for the GUI to catch
        raise FileNotFoundError(f"Input file not found at '{input_file_path}'")

    total_lines = 0
    total_merges = 0

    with open(input_file_path, 'r', encoding='utf-8') as infile, \
         open(output_file_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            total_lines += 1
            try:
                data = json.loads(line)
                
                # The 'conversations' field holds the list of turns
                if 'conversations' in data:
                    original_turns = data['conversations']
                    corrected_turns, merges = process_conversation(original_turns)
                    
                    data['conversations'] = corrected_turns
                    total_merges += merges
                
                # Write the corrected JSON object back to the new file
                outfile.write(json.dumps(data) + '\n')

            except json.JSONDecodeError:
                print(f"Warning: Skipping malformed JSON line at line number {total_lines}")
                continue

    print("\nCorrection complete!")
    print(f"Processed {total_lines} conversations.")
    print(f"Performed a total of {total_merges} merges.")
    print(f"Your corrected dataset is saved at: {output_file_path}")


def main():
    """
    Wrapper for running the script directly from the command line.
    """
    fix_consecutive_turns(
        input_file=_input_file_path_standalone,
        output_file=_output_file_path_standalone
    )


if __name__ == "__main__":
    main()