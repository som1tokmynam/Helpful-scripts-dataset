import json

def find_unused_text_chunks(master_file, resulting_file, output_file):
    """
    Loads a master and a resulting JSON file, finds text chunks present in
    the master but not in the resulting file, and saves them to an output file.

    Args:
        master_file (str): Path to the master JSON file (list of dicts).
        resulting_file (str): Path to the resulting JSON file (dict of dicts).
        output_file (str): Path to save the unused chunks to.
    """
    if not all([master_file, resulting_file, output_file]):
        raise ValueError("All file paths (master, resulting, and output) must be provided.")
        
    try:
        # Step 1: Load the master file
        # The master file is a list of dictionaries: [{"text": "..."}, {"text": "..."}]
        with open(master_file, 'r', encoding='utf-8') as f:
            master_data = json.load(f)
        print(f"Successfully loaded {len(master_data)} chunks from '{master_file}'.")

        # Step 2: Load the resulting file
        # The resulting file is a dictionary of dictionaries: {"0": {"text": "..."}, "1": {"text": "..."}}
        with open(resulting_file, 'r', encoding='utf-8') as f:
            resulting_data = json.load(f)
        print(f"Successfully loaded {len(resulting_data)} chunks from '{resulting_file}'.")

    except FileNotFoundError as e:
        print(f"Error: Could not find the file '{e.filename}'. Please ensure it's in the same directory.")
        raise e # Re-raise for the GUI to catch
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse a JSON file. Please check for syntax errors. Details: {e}")
        raise e # Re-raise for the GUI to catch

    # Step 3: Extract the text from both files into sets for efficient comparison.
    master_texts = {chunk['text'] for chunk in master_data if 'text' in chunk}
    resulting_texts = {item['text'] for item in resulting_data.values() if 'text' in item}

    # Step 4: Find the texts that are in the master set but NOT in the resulting set.
    unused_text_strings = master_texts - resulting_texts
    
    print(f"\nFound {len(unused_text_strings)} unused text passages.")

    # Step 5: Filter the original master list to get the full chunk objects
    # for the unused texts.
    unused_chunks = [
        chunk for chunk in master_data if 'text' in chunk and chunk['text'] in unused_text_strings
    ]

    # Step 6: Write the list of unused chunks to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Use indent=4 for a pretty, human-readable JSON output
        json.dump(unused_chunks, f, indent=4)
        
    print(f"Successfully wrote the {len(unused_chunks)} unused chunks to '{output_file}'.")
    print("Job complete!")