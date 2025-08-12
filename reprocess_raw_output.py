# reprocess_raw_output.py
import json
import re
import argparse
import os

# --- Core Parsing Logic (Unchanged) ---

def parse_chatlog(chatlog: str, all_charnames: list) -> list:
    """
    Parses a raw dialogue string into a structured list of turns.
    This definitive version correctly identifies turn ownership based on primary
    speakers ({user} or character names) and treats 'ooc:' as a neutral
    continuation of the current turn, not a new speaker.
    """
    messages = []
    if not chatlog:
        return messages

    current_turn_type = None
    current_turn_content = []

    def save_current_turn():
        """Helper to save the buffered turn to the messages list."""
        if current_turn_type and current_turn_content:
            full_content = "\n".join(current_turn_content).strip()
            if full_content:
                messages.append({
                    "from": current_turn_type,
                    "value": full_content
                })

    speaker_regex = re.compile(r"^\s*([^:\n]+?):\s*")

    for line in chatlog.split('\n'):
        stripped_line = line.strip()
        if not stripped_line:
            continue

        match = speaker_regex.match(stripped_line)
        
        line_owner = None

        if match:
            speaker_name = match.group(1).strip().lower()

            if speaker_name == "{user}":
                line_owner = "human"
            elif speaker_name == "ooc":
                line_owner = None
            else:
                line_owner = "gpt"
        
        if line_owner and line_owner != current_turn_type:
            save_current_turn()
            current_turn_type = line_owner
            current_turn_content = [stripped_line]
        else:
            if current_turn_type:
                current_turn_content.append(stripped_line)

    save_current_turn()
    return messages

# --- Main Reprocessing Function ---

def reprocess_raw_file(input_path: str, output_path: str):
    """
    Reads a raw pipeline output file, re-parses the 'story' field using the
    correct logic, and generates a final, clean ShareGPT file.
    """
    print(f"Reading raw data from: {input_path}")
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"FATAL: Input file not found at '{input_path}'")
        return
    except json.JSONDecodeError:
        print(f"FATAL: Could not parse JSON from '{input_path}'. The file may be corrupt.")
        return

    # <<< CHANGED: Using the exact prompt start and end you provided.
    rp_prompt_start = "You will act as a master Dungeon Master, guiding {user}, in a mature, long-form fantasy roleplay. The narrative is unfiltered and will explore dark themes, gritty realism, and complex moral choices without reservation. Prioritize a player-driven story with realistic consequences for his actions.\n\n"
    rp_prompt_end = "\n\nTake the role of a Dungeon master and roleplay with {user}.\nThen, the roleplay between {user} and the characters begins."

    final_sharegpt_data = []
    processed_count = 0
    skipped_count = 0

    for i, raw_obj in enumerate(raw_data):
        story_text = raw_obj.get("story")
        scene_card_text = raw_obj.get("scene_card")

        if not story_text or not scene_card_text:
            print(f"Warning: Skipping entry {i+1} due to missing 'story' or 'scene_card'.")
            skipped_count += 1
            continue

        # 1. Construct the system prompt
        system_prompt_value = f"{rp_prompt_start}{scene_card_text}{rp_prompt_end}"
        system_message = {"from": "system", "value": system_prompt_value}
        
        # 2. Parse the story text using the correct logic
        conversation_turns = parse_chatlog(story_text, [])

        # 3. Assemble the final ShareGPT object
        final_conversation = [system_message] + conversation_turns
        sharegpt_obj = {"conversations": final_conversation}
        
        final_sharegpt_data.append(sharegpt_obj)
        processed_count += 1

    print("-" * 20)
    print(f"Processing complete.")
    print(f"Successfully processed: {processed_count} entries.")
    print(f"Skipped: {skipped_count} entries.")

    # 4. Write the corrected data to the output file
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"Writing corrected ShareGPT data to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_sharegpt_data, f, indent=2)
    
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reprocesses raw pipeline output to generate a corrected ShareGPT file."
    )
    parser.add_argument(
        "-i", "--input-file",
        required=True,
        help="Path to the raw JSON output file (the one with the 'story' string)."
    )
    parser.add_argument(
        "-o", "--output-file",
        required=True,
        help="Path to write the new, corrected ShareGPT JSON file."
    )
    args = parser.parse_args()

    reprocess_raw_file(args.input_file, args.output_file)