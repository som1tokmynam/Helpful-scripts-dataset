# fix_turn_structure_final.py
import json
import sys
import re
from typing import List, Dict, Any, Tuple

# --- Constants for Role Identification ---
OOC_PATTERN = re.compile(r'^ooc:', re.IGNORECASE)
USER_TAG_PATTERN = re.compile(r'^\s*{user}:\s*', re.IGNORECASE)
NARRATOR_TAG_PATTERN = re.compile(r'^\s*{narrator}:\s*', re.IGNORECASE)
# Matches "Name:\n" or "Name:" at the start of a line
NAME_DELIMITER_PATTERN = re.compile(r'^\s*[A-Za-z][A-Za-z\s]+:\s*', re.MULTILINE)
# Matches "Name (Emotion): "dialogue"" - a strong GPT signal
DIALOGUE_PATTERN = re.compile(r'^\s*[A-Za-z\s]+\s*\([^)]+\):\s*".*', re.MULTILINE)


def pass_1_split_and_normalize(conversations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Pass 1: Splits turns containing multiple logical segments and assigns a preliminary,
    best-guess role based on content patterns.
    """
    processed_turns = []
    fixes_made = 0

    for turn in conversations:
        original_value = turn.get('value', '').strip()
        if not original_value:
            continue

        # Split by markers that indicate a new turn, keeping the marker.
        split_pattern = r'\n{2,}(?=(?:{user}:|{narrator}:|ooc:|' + NAME_DELIMITER_PATTERN.pattern + r'|' + DIALOGUE_PATTERN.pattern + r'))'
        segments = re.split(split_pattern, original_value, flags=re.IGNORECASE | re.MULTILINE)

        if len(segments) > 1:
            fixes_made += len(segments) - 1

        for segment_text in segments:
            segment_text = segment_text.strip()
            if not segment_text:
                continue
            
            # Assign a preliminary role based on content with priority
            role = turn['from']
            if USER_TAG_PATTERN.match(segment_text):
                role = 'human'
                segment_text = USER_TAG_PATTERN.sub('', segment_text).strip()
            elif (NAME_DELIMITER_PATTERN.match(segment_text) or 
                  DIALOGUE_PATTERN.match(segment_text) or
                  NARRATOR_TAG_PATTERN.match(segment_text)):
                role = 'gpt'
            
            if segment_text:
                processed_turns.append({'from': role, 'value': segment_text})

    return processed_turns, fixes_made


def pass_2_reconstruct_with_state(conversations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Pass 2: Rebuilds the conversation from scratch using a state machine.
    This enforces strict turn alternation for both narrative and OOC turns.
    """
    if not conversations:
        return [], 0

    final_turns = []
    fixes_made = 0
    
    # State variables
    last_narrative_speaker = 'system'
    last_overall_speaker = 'system'

    for turn in conversations:
        current_value = turn['value']
        is_ooc = bool(OOC_PATTERN.match(current_value))
        
        # Determine the ENFORCED role for this turn
        enforced_role = ''
        if is_ooc:
            # OOC role is the opposite of the last speaker, whoever it was.
            enforced_role = 'human' if last_overall_speaker == 'gpt' else 'gpt'
        else:
            # Narrative role is the opposite of the last NARRATIVE speaker.
            enforced_role = 'human' if last_narrative_speaker == 'gpt' else 'gpt'

        # Check if this turn can be merged with the previous one
        if (final_turns and 
            final_turns[-1]['from'] == enforced_role and
            bool(OOC_PATTERN.match(final_turns[-1]['value'])) == is_ooc):
            
            # Merge with previous turn
            final_turns[-1]['value'] += f"\n\n{current_value}"
            fixes_made += 1
        else:
            # Create a new turn with the enforced role
            if turn['from'] != enforced_role:
                fixes_made += 1 # A fix is counted if we had to change the role
            
            new_turn = {'from': enforced_role, 'value': current_value}
            final_turns.append(new_turn)

        # Update state variables
        last_overall_speaker = enforced_role
        if not is_ooc:
            last_narrative_speaker = enforced_role
            
    return final_turns, fixes_made


def fix_turn_structure(input_file: str, output_file: str):
    """
    Main function to process a JSONL file and fix conversation structures.
    """
    total_lines_read, total_lines_fixed, total_fixes_applied = 0, 0, 0
    print(f"Starting cleanup of '{input_file}'...")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for i, line in enumerate(infile):
            total_lines_read += 1
            try:
                data = json.loads(line)
                if 'conversations' not in data or not data['conversations']:
                    outfile.write(line)
                    continue
                
                system_prompt = data['conversations'][0]
                turns_to_process = data['conversations'][1:]
                
                # --- The Cleaning Pipeline ---
                pass1_turns, fixes1 = pass_1_split_and_normalize(turns_to_process)
                final_turns, fixes2 = pass_2_reconstruct_with_state(pass1_turns)
                
                total_fixes = fixes1 + fixes2
                if total_fixes > 0:
                    total_lines_fixed += 1
                    total_fixes_applied += total_fixes
                
                data['conversations'] = [system_prompt] + final_turns
                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

            except (json.JSONDecodeError, Exception) as e:
                print(f"Error on line {i+1}: {e}. Skipping line.", file=sys.stderr)
                outfile.write(line)

    print("\n--- Turn Structure Correction Complete ---")
    print(f"Total lines processed: {total_lines_read}")
    print(f"Conversations with fixes: {total_lines_fixed}")
    print(f"Total individual fixes applied: {total_fixes_applied}")
    print(f"Output written to: '{output_file}'")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_turn_structure.py <input_file.jsonl> <output_file.jsonl>")
        sys.exit(1)
    
    fix_turn_structure(sys.argv[1], sys.argv[2])