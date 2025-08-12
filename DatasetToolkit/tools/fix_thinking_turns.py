#!/usr/bin/env python3
import json
import argparse
import sys
import re

def split_collapsed_turns(conversations):
    """
    PASS 1: Finds and splits single 'gpt' turns that have been incorrectly merged
    with the subsequent 'human' choice and the NEXT 'gpt' thinking block.
    """
    split_conversations = []
    was_split = False
    for turn in conversations:
        if turn.get('from') != 'gpt':
            split_conversations.append(turn)
            continue

        value = turn.get('value', '')
        
        # Regex to find a user choice (e.g., "1. Some text.") that follows a </choices> tag
        # This is the signature of a collapsed turn.
        # It captures the user's choice and the start of the next thinking block.
        match = re.search(r'(</choices>\s*\n\s*)((\d+\.\s*.*?)\n(\s*<thinking>|\s*{narrator}))', value, re.DOTALL)

        if match:
            was_split = True
            
            # Part 1: The correct GPT response
            gpt_response_part = value[:match.start(1)] + match.group(1)
            split_conversations.append({'from': 'gpt', 'value': gpt_response_part.strip()})
            
            # Part 2: The human choice
            human_choice_part = match.group(3).strip()
            split_conversations.append({'from': 'human', 'value': human_choice_part})
            
            # Part 3: The rest of the string, which is the NEXT GPT response
            next_gpt_part = value[match.start(4):]
            split_conversations.append({'from': 'gpt', 'value': next_gpt_part.strip()})
        else:
            split_conversations.append(turn)
            
    return split_conversations, was_split


def merge_misplaced_thinking_blocks(conversations):
    """
    PASS 2: Finds and merges a misplaced 'human' turn (containing a thinking block)
    into the correct 'gpt' turn. This is the logic from the V3 script.
    """
    merged_conversations = []
    i = 0
    was_merged = False
    
    while i < len(conversations):
        if i + 2 < len(conversations):
            turn1, turn2, turn3 = conversations[i], conversations[i+1], conversations[i+2]
            
            t1_from = turn1.get('from', '')
            t1_val = turn1.get('value', '').strip()
            t2_from = turn2.get('from', '')
            t2_val = turn2.get('value', '').strip()
            t3_from = turn3.get('from', '')

            is_pattern = (
                t1_from == 'gpt' and t1_val == '<thinking>' and
                t2_from == 'human' and t2_val.endswith('</thinking>') and not t2_val.startswith('<thinking>') and
                t3_from == 'gpt'
            )

            if is_pattern:
                was_merged = True
                thinking_block = f"<thinking>\n{turn2.get('value', '').strip()}\n"
                main_response = turn3.get('value', '')
                combined_value = f"{thinking_block}{main_response}"
                
                merged_conversations.append({'from': 'gpt', 'value': combined_value})
                i += 3
                continue

        merged_conversations.append(conversations[i])
        i += 1
        
    return merged_conversations, was_merged


def process_jsonl_file(input_path, output_path):
    """
    Reads a JSONL file, applies a two-pass fix to the conversations,
    and writes the corrected data to a new file.
    """
    lines_processed = 0
    records_fixed = 0
    
    try:
        print(f"Reading from: {input_path}")
        print(f"Writing to:   {output_path}\n")
        
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                lines_processed += 1
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON on line {lines_processed}: {line.strip()}", file=sys.stderr)
                    outfile.write(line)
                    continue

                if 'conversations' in data and isinstance(data['conversations'], list):
                    # --- TWO-PASS FIXING PROCESS ---
                    original_conversations = data['conversations']
                    
                    # Pass 1: Split any collapsed GPT turns
                    pass1_conversations, was_split = split_collapsed_turns(original_conversations)
                    
                    # Pass 2: Merge any misplaced thinking blocks
                    pass2_conversations, was_merged = merge_misplaced_thinking_blocks(pass1_conversations)
                    
                    if was_split or was_merged:
                        records_fixed += 1
                        data['conversations'] = pass2_conversations
                
                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        return

    print("---")
    print("Processing complete.")
    print(f"Total lines (records) processed: {lines_processed}")
    print(f"Total records fixed: {records_fixed}")
    if records_fixed > 0:
        print("\nSuccess! The script found and corrected malformed records.")
        print("Both 'collapsed turns' and 'misplaced thinking blocks' have been fixed.")
    else:
        print("\nNote: The script ran successfully but did not find any records to fix.")


def main():
    parser = argparse.ArgumentParser(
        description="Fixes complex structural errors in a JSONL conversation dataset (Version 4).",
        epilog="This script fixes two types of errors:\n"
               "1. 'Collapsed Turns': A single GPT turn that incorrectly contains the next HUMAN and GPT turns.\n"
               "2. 'Misplaced Thinking Blocks': A HUMAN turn that incorrectly contains a GPT thinking block.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_file", help="Path to the source JSONL file you want to fix.")
    parser.add_argument("output_file", help="Path to write the corrected JSONL file.")
    
    args = parser.parse_args()
    
    process_jsonl_file(args.input_file, args.output_file)

if __name__ == "__main__":
    main()