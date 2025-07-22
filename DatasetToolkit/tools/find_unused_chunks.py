import json

# --- Configuration ---
# You can change these file names if needed
MASTER_FILE = 'chunk_cache_edee4f7ed42f42b5a8f3b49ca9f9b90d_size2000.json'
RESULTING_FILE = 'story_generation.json'
OUTPUT_FILE = 'unused_chunks.json'

def find_unused_text_chunks():
    """
    Loads a master and a resulting JSON file, finds text chunks present in
    the master but not in the resulting file, and saves them to an output file.
    """
    try:
        # Step 1: Load the master file
        # The master file is a list of dictionaries: [{"text": "..."}, {"text": "..."}]
        with open(MASTER_FILE, 'r', encoding='utf-8') as f:
            master_data = json.load(f)
        print(f"Successfully loaded {len(master_data)} chunks from '{MASTER_FILE}'.")

        # Step 2: Load the resulting file
        # The resulting file is a dictionary of dictionaries: {"0": {"text": "..."}, "1": {"text": "..."}}
        with open(RESULTING_FILE, 'r', encoding='utf-8') as f:
            resulting_data = json.load(f)
        print(f"Successfully loaded {len(resulting_data)} chunks from '{RESULTING_FILE}'.")

    except FileNotFoundError as e:
        print(f"Error: Could not find the file '{e.filename}'. Please ensure it's in the same directory.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse a JSON file. Please check for syntax errors. Details: {e}")
        return

    # Step 3: Extract the text from both files into sets for efficient comparison.
    # Using a set allows for very fast lookups.
    
    # Extract text from the master list
    master_texts = {chunk['text'] for chunk in master_data}
    
    # Extract text from the resulting dictionary's values
    resulting_texts = {item['text'] for item in resulting_data.values()}

    # Step 4: Find the texts that are in the master set but NOT in the resulting set.
    # This is the core logic: a simple set difference.
    unused_text_strings = master_texts - resulting_texts
    
    print(f"\nFound {len(unused_text_strings)} unused text passages.")

    # Step 5: Filter the original master list to get the full chunk objects
    # for the unused texts. This preserves the original structure (including metadata).
    unused_chunks = [
        chunk for chunk in master_data if chunk['text'] in unused_text_strings
    ]

    # Step 6: Write the list of unused chunks to the output file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # Use indent=4 for a pretty, human-readable JSON output
        json.dump(unused_chunks, f, indent=4)
        
    print(f"Successfully wrote the {len(unused_chunks)} unused chunks to '{OUTPUT_FILE}'.")
    print("Job complete!")


# Run the main function when the script is executed
if __name__ == "__main__":
    find_unused_text_chunks()