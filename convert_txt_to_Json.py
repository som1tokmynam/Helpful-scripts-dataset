import json
import os
import glob

def convert_multiple_txt_to_json(input_directory, output_file_path):
    """
    Finds all .txt files in a directory, reads their content, and converts them 
    into a single JSON file containing a list of objects.

    Args:
      input_directory: The path to the folder containing the .txt files.
      output_file_path: The path for the final combined .json file.
    """
    # This list will hold the content of all your files
    all_data = []

    # Create the full path for searching for .txt files
    # The '*' is a wildcard that matches any characters
    search_path = os.path.join(input_directory, '*.txt')

    # glob.glob finds all pathnames matching a specified pattern
    txt_file_paths = glob.glob(search_path)
    
    if not txt_file_paths:
        print(f"Warning: No .txt files were found in the directory '{input_directory}'.")
        return

    print(f"Found {len(txt_file_paths)} .txt files to convert.")

    # Loop through each file path we found
    for file_path in txt_file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as txt_file:
                # Read the entire content of the file
                file_content = txt_file.read()
                
                # Create the dictionary in the desired format
                data_entry = {
                    "text": file_content
                }
                
                # Add the dictionary to our list
                all_data.append(data_entry)
                print(f"Successfully processed: {file_path}")

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    # Write the entire list of data to the output JSON file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            # json.dump writes the list to the file
            # indent=2 makes the JSON file human-readable
            json.dump(all_data, json_file, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Success! All files have been combined into {output_file_path}")
        
    except Exception as e:
        print(f"\n❌ Error writing to JSON file: {e}")


# --- Configuration ---
# The folder where your 19 .txt files are located.
# This should match the folder you created in Step 1.
INPUT_FOLDER_NAME = 'source_text_files' 

# The name you want for your final, combined JSON file.
OUTPUT_JSON_NAME = 'combined_output.json'

# --- Run the Conversion ---
convert_multiple_txt_to_json(INPUT_FOLDER_NAME, OUTPUT_JSON_NAME)