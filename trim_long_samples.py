import json
from transformers import AutoTokenizer

# --- SCRIPT CONFIGURATION ---
MODEL_PATH = "meta-llama/Llama-3.3-70B-Instruct"  # The path to your base model's tokenizer
INPUT_FILE = "cleaned_incredible_stories_list_sharegpt.jsonl" # Your input file
OUTPUT_FILE = "cleaned_incredible_stories_list_sharegpt_trimmed.jsonl"    # The new, corrected file that will be created
MAX_LENGTH = 8192                        # Your Axolotl max_seq_length
# --- END CONFIGURATION ---

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
special_tokens_to_add = ["<thinking>", "</thinking>", "<choices>", "</choices>"]
tokenizer.add_special_tokens({"additional_special_tokens": special_tokens_to_add})
print(f"Tokenizer loaded. Special tokens added. Max length set to {MAX_LENGTH}.")

# This function does the core work on a single conversation
def trim_conversation(conversation, max_len, tk):
    # --- START OF MODIFICATION ---
    # Temporarily convert ShareGPT format to the format the tokenizer's chat template expects
    formatted_for_tokenizer = []
    for turn in conversation:
        role = ""
        if turn['from'] == 'human':
            role = 'user'
        elif turn['from'] == 'gpt':
            role = 'assistant'
        else:
            role = turn['from'] # Handles 'system'
        formatted_for_tokenizer.append({'role': role, 'content': turn['value']})
    # --- END OF MODIFICATION ---

    # Calculate the initial length using the correctly formatted data
    full_prompt = tk.apply_chat_template(formatted_for_tokenizer, tokenize=False) # <--- MODIFICATION
    initial_tokens = len(tk.encode(full_prompt))

    if initial_tokens <= max_len:
        return conversation, initial_tokens # No changes needed

    system_turn = conversation[0] if conversation[0]['from'] == 'system' else None
    start_index = 1 if system_turn else 0
    middle_turns = conversation[start_index:-2]
    last_two_turns = conversation[-2:]

    if not last_two_turns or not (last_two_turns[0]['from'] == 'human' and last_two_turns[1]['from'] == 'gpt'):
        print(f"  [WARNING] Row does not end in a human/gpt pair. Cannot trim safely. Original tokens: {initial_tokens}")
        return None, 0

    current_tokens = initial_tokens
    
    while current_tokens > max_len and len(middle_turns) > 0:
        # Remove turns in pairs (human and gpt) to keep context logical
        del middle_turns[:2]

        # --- START OF MODIFICATION ---
        # Reassemble and re-check length, again using the temporary format
        temp_convo_original = ([system_turn] if system_turn else []) + middle_turns + last_two_turns
        
        # Convert the newly trimmed conversation for tokenization
        temp_formatted_for_tokenizer = []
        for turn in temp_convo_original:
            role = ""
            if turn['from'] == 'human':
                role = 'user'
            elif turn['from'] == 'gpt':
                role = 'assistant'
            else:
                role = turn['from']
            temp_formatted_for_tokenizer.append({'role': role, 'content': turn['value']})

        current_tokens = len(tk.encode(tk.apply_chat_template(temp_formatted_for_tokenizer, tokenize=False)))
        # --- END OF MODIFICATION ---

    if current_tokens > max_len:
        return None, current_tokens

    final_convo = ([system_turn] if system_turn else []) + middle_turns + last_two_turns
    return final_convo, current_tokens

# --- Main Processing Loop (Unchanged) ---
print(f"\nProcessing {INPUT_FILE}...")
original_count = 0
processed_count = 0
dropped_count = 0

with open(INPUT_FILE, 'r', encoding='utf-8') as infile, open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
    for i, line in enumerate(infile):
        original_count += 1
        try:
            data = json.loads(line)
            conversation = data["conversations"]

            trimmed_convo, final_len = trim_conversation(conversation, MAX_LENGTH, tokenizer)

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
        except KeyError:
            print(f"  - Row {i+1}: Skipping due to missing 'conversations' key.")
            dropped_count += 1

print(f"\nDone. Processed {original_count} rows.")
print(f"Wrote {processed_count} valid rows to {OUTPUT_FILE}.")
print(f"Dropped {dropped_count} rows.")