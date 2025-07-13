import json
from pathlib import Path

def load_jsonl(file_path):
    """Loads data from a JSONL file."""
    data = []
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        for line in file:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON line: {line.strip()}. Error: {e}")
    return data

def load_filter_criteria(filter_files):
    """Loads filter phrases from a list of text files."""
    filter_criteria = set()
    for filter_file in filter_files:
        with open(filter_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line:
                    filter_criteria.add(stripped_line)
    return list(filter_criteria)

def filter_conversations(conversations, filter_criteria, threshold=None):
    """
    Filters conversations based on one of two modes:
    1. If threshold is None: Removes any conversation with at least one slop phrase.
    2. If threshold is a float: Removes conversations where the slop phrase count
       is >= (average slop phrases per conversation * threshold).
    """
    if not filter_criteria:
        print("Warning: Filter criteria is empty. No conversations will be removed.")
        return conversations, 0

    clean_conversations = []
    removed_count = 0

    if threshold is None:
        print("[*] Filtering mode: Remove any conversation with a matched phrase.")
        for conv in conversations:
            found_slop = False
            for msg in conv.get("conversations", []):
                if msg.get("from") == "gpt" and isinstance(msg.get("value"), str):
                    if any(phrase in msg["value"] for phrase in filter_criteria):
                        found_slop = True
                        break
            if found_slop:
                removed_count += 1
            else:
                clean_conversations.append(conv)
        return clean_conversations, removed_count
    else:
        print(f"[*] Filtering mode: Threshold-based removal (threshold = {threshold}).")
        
        matched_counts = []
        total_matched_phrases = 0
        for conv in conversations:
            phrases_in_conv = 0
            for msg in conv.get("conversations", []):
                if msg.get("from") == "gpt" and isinstance(msg.get("value"), str):
                    phrases_in_conv += sum(1 for phrase in filter_criteria if phrase in msg["value"])
            matched_counts.append(phrases_in_conv)
            total_matched_phrases += phrases_in_conv
            
        if not conversations or total_matched_phrases == 0:
            print("No filter phrases were found in the dataset. No conversations removed.")
            return conversations, 0
            
        avg_phrases = total_matched_phrases / len(conversations)
        removal_threshold_count = avg_phrases * threshold
        print(f"    - Average matched phrases per entry: {avg_phrases:.2f}")
        print(f"    - Removal threshold (count >=): {removal_threshold_count:.2f}")

        for i, conv in enumerate(conversations):
            if matched_counts[i] >= removal_threshold_count:
                removed_count += 1
            else:
                clean_conversations.append(conv)
        
        return clean_conversations, removed_count

def write_filtered_jsonl(filtered_data, output_file_path):
    """Writes the filtered data to a new JSONL file."""
    # Ensure the parent directory exists, without creating the tool's own sub-folder
    Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for conversation in filtered_data:
            json.dump(conversation, file, ensure_ascii=False)
            file.write('\n')

# --- CHANGE: Simplified function signature and logic ---
def filter_dataset(dataset_file, output_file, filter_files, threshold=None):
    """Main function to orchestrate the deslopping process."""
    if not dataset_file or not output_file or not filter_files or not filter_files[0]:
        raise ValueError("Input dataset, output file, and filter file must all be specified.")

    filter_criteria = load_filter_criteria(filter_files)
    original_data = load_jsonl(dataset_file)
    
    filtered_data, removed_count = filter_conversations(original_data, filter_criteria, threshold=threshold)

    # Directly write to the specified output file
    write_filtered_jsonl(filtered_data, output_file)

    print("\n[+] Deslopping Complete!")
    print(f"    Original conversations: {len(original_data)}")
    print(f"    Conversations removed: {removed_count}")
    print(f"    Remaining conversations: {len(filtered_data)}")
    print(f"    Filtered output written to: {output_file}")