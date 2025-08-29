# tools/trim_long_samples.py

import json
import sys
import os
from transformers import AutoTokenizer, PreTrainedTokenizer

def _format_for_tokenizer(conversation: list[dict]) -> list[dict]:
    """Converts ShareGPT format to the format the tokenizer's chat template expects."""
    formatted_for_tokenizer = []
    for turn in conversation:
        role = turn.get('from', 'unknown')
        if role == 'human':
            role = 'user'
        elif role == 'gpt':
            role = 'assistant'
        # Handles 'system' and any other roles directly
        formatted_for_tokenizer.append({'role': role, 'content': turn.get('value', '')})
    return formatted_for_tokenizer

def trim_conversation(conversation: list[dict], max_len: int, tk: PreTrainedTokenizer) -> tuple[list[dict] | None, int]:
    """
    Trims a conversation from the middle to fit within a specified token length.

    Args:
        conversation: The original conversation in ShareGPT format.
        max_len: The maximum allowed token length.
        tk: The tokenizer instance.

    Returns:
        A tuple containing the trimmed conversation (or None if it cannot be trimmed)
        and the final token count.
    """
    temp_formatted = _format_for_tokenizer(conversation)
    initial_tokens = len(tk.encode(tk.apply_chat_template(temp_formatted, tokenize=False)))

    if initial_tokens <= max_len:
        return conversation, initial_tokens  # No changes needed

    # Preserve system prompt (if any) and the last two turns
    system_turn = conversation[0] if conversation and conversation[0].get('from') == 'system' else None
    start_index = 1 if system_turn else 0
    
    if len(conversation) < start_index + 2:
        print(f"  [WARNING] Not enough turns to trim safely. Original tokens: {initial_tokens}")
        return None, initial_tokens

    middle_turns = conversation[start_index:-2]
    last_two_turns = conversation[-2:]

    if not (last_two_turns[0].get('from') == 'human' and last_two_turns[1].get('from') == 'gpt'):
        print(f"  [WARNING] Row does not end in a human/gpt pair. Cannot trim safely. Original tokens: {initial_tokens}")
        return None, initial_tokens

    current_tokens = initial_tokens
    
    # Remove turns from the middle in pairs (human and gpt) to keep context logical
    while current_tokens > max_len and len(middle_turns) >= 2:
        del middle_turns[:2]
        temp_convo_original = ([system_turn] if system_turn else []) + middle_turns + last_two_turns
        temp_formatted_for_tokenizer = _format_for_tokenizer(temp_convo_original)
        current_tokens = len(tk.encode(tk.apply_chat_template(temp_formatted_for_tokenizer, tokenize=False)))

    if current_tokens > max_len:
        return None, current_tokens

    final_convo = ([system_turn] if system_turn else []) + middle_turns + last_two_turns
    return final_convo, current_tokens

def trim_long_samples_main(input_file: str, output_file: str, max_length: int, model_path: str):
    """
    Main function to process a JSONL file, trimming long conversations.
    """
    # --- Logic to find the correct tokenizer path ---
    tokenizer_load_path = model_path
    try:
        # Check if the script is running in a PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # sys._MEIPASS is the path to the temporary folder where PyInstaller unpacks the app
            bundle_dir = sys._MEIPASS
            # This is the path to the 'local_tokenizer' folder we added in the .spec file
            local_tokenizer_path = os.path.join(bundle_dir, 'local_tokenizer')
            
            if os.path.isdir(local_tokenizer_path):
                 tokenizer_load_path = local_tokenizer_path
                 print(f"INFO: Running in bundled app. Using local tokenizer from: {tokenizer_load_path}")
            else:
                 print(f"WARNING: Running in bundled app, but local tokenizer folder not found at {local_tokenizer_path}. Falling back to Hub.")
        else:
            print(f"INFO: Running as a standard Python script. Using tokenizer from Hub: {model_path}")

    except Exception as e:
        print(f"WARNING: Could not determine bundle path, falling back to Hub model path. Error: {e}")
    # --- End of tokenizer path logic ---

    print("Loading tokenizer...")
    try:
        # Use the determined path to load the tokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_load_path)
        special_tokens_to_add = ["<thinking>", "</thinking>", "<choices>", "</choices>"]
        tokenizer.add_special_tokens({"additional_special_tokens": special_tokens_to_add})
        print(f"Tokenizer '{os.path.basename(tokenizer_load_path)}' loaded. Max length set to {max_length}.")
    except Exception as e:
        print(f"FATAL: Could not load tokenizer from '{tokenizer_load_path}'. Please ensure the path is correct or you have internet access. Error: {e}", file=sys.stderr)
        raise

    print(f"\nProcessing {input_file}...")
    original_count = 0
    processed_count = 0
    dropped_count = 0

    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for i, line in enumerate(infile):
            original_count += 1
            try:
                data = json.loads(line)
                conversation = data.get("conversations")
                if not conversation:
                    raise KeyError("Missing 'conversations' key.")

                trimmed_convo, final_len = trim_conversation(conversation, max_length, tokenizer)

                if trimmed_convo:
                    data['conversations'] = trimmed_convo
                    outfile.write(json.dumps(data) + "\n")
                    processed_count += 1
                else:
                    dropped_count += 1
                    if dropped_count <= 20: # Print info for the first few dropped
                        print(f"  - Row {i+1}: Dropped. Still too long ({final_len} tokens) even after trimming.")
            
            except json.JSONDecodeError:
                print(f"  - Row {i+1}: Skipping due to JSON decoding error.")
                dropped_count += 1
            except KeyError as e:
                print(f"  - Row {i+1}: Skipping due to {e}.")
                dropped_count += 1
            except Exception as e:
                print(f"  - Row {i+1}: An unexpected error occurred: {e}")
                dropped_count += 1

    print(f"\nDone. Processed {original_count} rows.")
    print(f"Wrote {processed_count} valid rows to {output_file}.")
    print(f"Dropped {dropped_count} rows.")