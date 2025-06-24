import json

def count_characters_in_jsonl(input_file: str):
    """
    Reads a JSONL file and calculates character count statistics for its content.
    It intelligently handles formats with a "text" key or a "conversations" list.
    
    Args:
        input_file (str): Path to the input .jsonl file.
    """
    if not input_file:
        raise ValueError("An input file must be specified.")

    print(f"[*] Analyzing character counts for: {input_file}")
    
    total_entries = 0
    skipped_entries = 0
    total_chars = 0
    min_chars = float('inf')
    max_chars = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            for i, line in enumerate(infile, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    char_count = 0
                    
                    # Case 1: Simple {"text": "..."} format
                    if 'text' in data and isinstance(data.get('text'), str):
                        char_count = len(data['text'])
                    
                    # Case 2: {"conversations": [...]} format
                    elif 'conversations' in data and isinstance(data.get('conversations'), list):
                        # Sum characters from all 'value' fields in the conversation
                        char_count = sum(
                            len(turn.get('value', '')) 
                            for turn in data['conversations'] 
                            if isinstance(turn.get('value'), str)
                        )
                    else:
                        print(f"Warning: Skipping line {i} with unrecognized format.")
                        skipped_entries += 1
                        continue
                        
                    # Update statistics
                    total_entries += 1
                    total_chars += char_count
                    min_chars = min(min_chars, char_count)
                    max_chars = max(max_chars, char_count)

                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON on line {i}.")
                    skipped_entries += 1
                    
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if total_entries == 0:
        print("\n[!] No valid entries found to analyze.")
        return
        
    avg_chars = total_chars / total_entries
    
    print("\n[+] Character Count Analysis Complete!")
    print("---------------------------------------")
    print(f"  Total Entries Processed: {total_entries:,}")
    print(f"  Total Characters:        {total_chars:,}")
    print(f"  Average Chars/Entry:     {avg_chars:,.2f}")
    print(f"  Min Chars in an Entry:   {min_chars:,}")
    print(f"  Max Chars in an Entry:   {max_chars:,}")
    print(f"  Skipped/Invalid Lines:   {skipped_entries:,}")
    print("---------------------------------------")