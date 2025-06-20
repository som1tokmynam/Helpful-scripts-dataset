import json
import argparse
import sys

def main(args):
    """
    Main function to process the JSONL file.
    Reads a JSONL file, removes the last turn if it's from the user,
    and writes the result to a new file.
    """
    # Use configuration from parsed arguments
    input_file_path = args.input_file
    output_file_path = args.output_file
    conversation_key = args.conversation_key
    role_key = args.role_key
    user_role_name = args.user_role

    print(f"[*] Starting to process file: {input_file_path}")
    print(f"    - User role to check for: '{user_role_name}'")
    print(f"    - Output will be saved to: {output_file_path}")

    # Keep track of how many conversations are modified
    cleaned_count = 0
    total_count = 0
    skipped_empty_count = 0

    try:
        # Open the input and output files
        with open(input_file_path, 'r', encoding='utf-8') as infile, \
             open(output_file_path, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                total_count += 1
                
                # Load the JSON object from the line
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON line {total_count}: {line.strip()}", file=sys.stderr)
                    continue

                # Check if the conversation data is valid and non-empty
                if conversation_key in data and data[conversation_key] and isinstance(data[conversation_key], list):
                    # Check the role of the last turn
                    last_turn = data[conversation_key][-1]
                    if isinstance(last_turn, dict) and last_turn.get(role_key) == user_role_name:
                        # If the last turn is from the user, remove it
                        data[conversation_key] = data[conversation_key][:-1]
                        cleaned_count += 1

                # Write the (potentially modified) data to the new file,
                # but only if the conversation list is not empty after cleaning.
                if data.get(conversation_key):
                     outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
                else:
                     skipped_empty_count += 1
                     print(f"Info: Skipping conversation from line {total_count} as it became empty after cleaning.")

        print("\n[+] Processing Complete")
        print(f"    Total conversations read: {total_count}")
        print(f"    Conversations cleaned (last user turn removed): {cleaned_count}")
        print(f"    Conversations skipped (became empty): {skipped_empty_count}")
        print(f"    Cleaned data saved to: {output_file_path}")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file_path}'", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    # --- Argument Parser Setup ---
    parser = argparse.ArgumentParser(
        description="Clean a JSONL file by removing the last turn of a conversation if it's from the user.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Shows default values in help
    )

    # --- Positional Arguments (Required) ---
    parser.add_argument(
        "input_file",
        help="Path to the input JSONL file to be cleaned."
    )
    parser.add_argument(
        "output_file",
        help="Path to save the cleaned output JSONL file."
    )

    # --- Optional Arguments (with defaults from your original script) ---
    parser.add_argument(
        "--conversation-key",
        default="conversations",
        help="The JSON key for the list of conversation turns."
    )
    parser.add_argument(
        "--role-key",
        default="from",
        help="The JSON key within a turn object that specifies the role."
    )
    parser.add_argument(
        "--user-role",
        default="human",
        help="The value of the role key that identifies the user."
    )
    
    # Parse the arguments from the command line
    args = parser.parse_args()
    
    # Run the main logic
    main(args)