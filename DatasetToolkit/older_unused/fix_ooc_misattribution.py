import json
import sys
import re

def is_junk(turn):
    """
    A definitive helper function to identify and flag all known types of junk turns.
    This function is robust against missing keys, non-string, and empty/whitespace values.
    """
    if not isinstance(turn, dict): return True
    value = turn.get('value')
    if not isinstance(value, str): return True
    value_stripped = value.strip()
    if not value_stripped: return True
    value_lower = value_stripped.lower()
    
    # Check for simple OOC/user markers that should be removed
    if value_lower in ['ooc:', 'ooc: {user}:', '{user}:']: return True
    
    # --- MODIFIED: Fix for Issue #1 ---
    # Catches empty speaker turns (e.g., "Firestorm:") from ANY speaker, not just 'gpt'.
    # The split length is set to < 4 to safely catch single or multi-word names.
    if value_lower.endswith(':') and len(value_stripped.split()) < 4: 
        return True
        
    return False

def fix_dataset_issues(input_file: str, output_file: str):
    """
    Reads a JSONL file and applies a definitive multi-stage cleaning and repair process
    to the 'conversations' list in each line.
    """
    if not input_file or not output_file:
        print("Error: Input and Output file paths must be provided.")
        return

    total_lines_read, total_fixes_applied = 0, 0
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:

            for i, line in enumerate(infile):
                total_lines_read += 1
                line_num = i + 1
                fixes_this_line = 0

                try:
                    data = json.loads(line)
                    if 'conversations' not in data or not isinstance(data.get('conversations'), list):
                        outfile.write(line)
                        continue

                    original_turns = data['conversations']
                    
                    # --- Stage 1: Pre-Scrub - Remove all known junk turns ---
                    pass1_turns = [turn for turn in original_turns if not is_junk(turn)]
                    if len(pass1_turns) < len(original_turns):
                        fixes_this_line += (len(original_turns) - len(pass1_turns))

                    # --- Stage 2A: Iterative Split - Split turns with multiple speaker blocks ---
                    pass2a_turns = []
                    split_pattern = r'(\n\n\{narrator\}:|\n\n\{user\}:)'
                    for turn in pass1_turns:
                        value = turn.get('value', '')
                        if re.search(split_pattern, value):
                            parts = re.split(split_pattern, value)
                            if parts[0].strip():
                                pass2a_turns.append({'from': turn.get('from'), 'value': parts[0].strip()})
                            for j in range(1, len(parts), 2):
                                marker, content = parts[j], parts[j+1]
                                if marker and content.strip():
                                    reconstructed_value = (marker + content).strip()
                                    pass2a_turns.append({'from': turn.get('from'), 'value': reconstructed_value})
                            fixes_this_line += 1
                        else:
                            pass2a_turns.append(turn)

                    # --- Stage 2B: Structural Repair - Split merged turns ---
                    pass2b_turns = []
                    ooc_qna_split_marker = '\n{narrator}:\nooc:'
                    human_ooc_split_marker = '\nooc:'
                    for turn in pass2a_turns:
                        value, from_who = turn.get('value', ''), turn.get('from')
                        gpt_marker_pos = value.find(ooc_qna_split_marker)
                        if from_who == 'gpt' and gpt_marker_pos != -1:
                            before_narrator_part = value[:gpt_marker_pos].strip()
                            narrator_content = value[gpt_marker_pos + len(ooc_qna_split_marker):].strip()
                            human_marker_pos = before_narrator_part.rfind(human_ooc_split_marker)
                            if human_marker_pos != -1:
                                ic_part, human_question_part = before_narrator_part[:human_marker_pos].strip(), before_narrator_part[human_marker_pos:].strip()
                                if ic_part: pass2b_turns.append({'from': 'gpt', 'value': ic_part})
                                if human_question_part: pass2b_turns.append({'from': 'human', 'value': human_question_part})
                            else:
                                if before_narrator_part: pass2b_turns.append({'from': 'human', 'value': before_narrator_part})
                            if narrator_content:
                                narrator_full_response = f"{{narrator}}:\nooc:{narrator_content}"
                                pass2b_turns.append({'from': 'gpt', 'value': narrator_full_response})
                            fixes_this_line += 1
                        else:
                            pass2b_turns.append(turn)

                    # --- NEW STAGE 2C: Split OOC from IC - Fix for Issue #2 ---
                    # This stage handles cases where an OOC comment is merged with narrative text.
                    # e.g., "ooc: Resuming scene.\n\n*The character walks..."
                    pass2c_turns = []
                    for turn in pass2b_turns:
                        value = turn.get('value', '').strip()
                        from_who = turn.get('from')
                        
                        if from_who == 'gpt' and value.lower().startswith('ooc:') and '\n\n' in value:
                            split_pos = value.find('\n\n')
                            ooc_part = value[:split_pos].strip()
                            ic_part = value[split_pos:].strip()
                            
                            if ooc_part and ic_part:
                                pass2c_turns.append({'from': 'gpt', 'value': ooc_part})
                                pass2c_turns.append({'from': 'gpt', 'value': ic_part})
                                fixes_this_line += 1
                                continue
                        
                        pass2c_turns.append(turn)
                    
                    # --- Stage 3: Turn-Level Correction & Normalization ---
                    pass3_turns = []
                    for turn in pass2c_turns: # Input from the new stage
                        new_turn = turn.copy()
                        value = new_turn.get('value', '').strip()
                        if new_turn.get('from') == 'gpt' and 'Understood' in value:
                            new_turn['from'] = 'human'; fixes_this_line += 1
                        elif new_turn.get('from') == 'gpt' and value.lower().startswith('ooc: {narrator}:'):
                            last_ooc_pos = value.lower().rfind('ooc:')
                            content = value[last_ooc_pos + 4:].strip()
                            new_turn['value'] = f"{{narrator}}:\nooc: {content}"; fixes_this_line += 1
                        pass3_turns.append(new_turn)

                    # --- Stage 4: OOC Tag Grouping ---
                    pass4_turns = []
                    i = 0
                    while i < len(pass3_turns):
                        current_turn = pass3_turns[i]
                        value = current_turn.get('value', '').strip()
                        is_ooc_start = ('what are' in value.lower() and 'motives' in value.lower() and current_turn.get('from') == 'human')
                        if is_ooc_start and i + 2 < len(pass3_turns):
                            processed_any = False
                            for j in range(3):
                                turn_to_process = pass3_turns[i+j]
                                clean_val = turn_to_process.get('value', '').strip()
                                if clean_val.lower().startswith('ooc:'): clean_val = clean_val[4:].lstrip()
                                if clean_val:
                                    processed_turn = { 'from': turn_to_process.get('from'), 'value': f'ooc: {clean_val}' }
                                    pass4_turns.append(processed_turn); processed_any = True
                            if processed_any: fixes_this_line += 1
                            i += 3
                        else:
                            pass4_turns.append(current_turn); i += 1
                            
                    # --- Stage 5: OOC Attribution Correction ---
                    pass5_turns = []
                    i = 0
                    num_turns_s4 = len(pass4_turns)
                    while i < num_turns_s4:
                        current_turn = pass4_turns[i]
                        current_value = current_turn.get('value', '').strip()
                        if current_value.lower().startswith('ooc:'):
                            block_start_index, block_end_index = i, i
                            while (block_end_index + 1 < num_turns_s4 and
                                   pass4_turns[block_end_index + 1].get('value', '').strip().lower().startswith('ooc:')):
                                block_end_index += 1
                            ooc_block = pass4_turns[block_start_index : block_end_index + 1]
                            has_human_turn = any(turn.get('from') == 'human' for turn in ooc_block)
                            if not has_human_turn and ooc_block:
                                first_turn = ooc_block[0]
                                if first_turn.get('from') == 'gpt':
                                    corrected_turn = first_turn.copy()
                                    corrected_turn['from'] = 'human'
                                    pass5_turns.append(corrected_turn)
                                    fixes_this_line += 1
                                    pass5_turns.extend(ooc_block[1:])
                                else:
                                    pass5_turns.extend(ooc_block)
                            else:
                                pass5_turns.extend(ooc_block)
                            i = block_end_index + 1
                        else:
                            pass5_turns.append(current_turn)
                            i += 1

                    # --- Stage 6: Post-Scrub - Final removal of any turns that became junk ---
                    initial_count = len(pass5_turns)
                    final_turns = [turn for turn in pass5_turns if not is_junk(turn)]
                    if initial_count != len(final_turns): fixes_this_line += (initial_count - len(final_turns))

                    if fixes_this_line > 0:
                        print(f"Applied {fixes_this_line} fix(es) to conversation on line {line_num}.")
                        total_fixes_applied += fixes_this_line
                    
                    data['conversations'] = final_turns
                    outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

                except json.JSONDecodeError:
                    print(f"Warning: Line {line_num} is not valid JSON. Copying as-is.")
                    outfile.write(line)

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file}'"); sys.exit(1)

    print("\n--- Processing Complete ---")
    print(f"Total lines read: {total_lines_read}")
    print(f"Total individual corrections applied: {total_fixes_applied}")
    print(f"Corrected data written to: '{output_file}'")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_ooc_misattribution.py <input_file.jsonl> <output_file.jsonl>")
    else:
        fix_dataset_issues(sys.argv[1], sys.argv[2])