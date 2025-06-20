# tools/convert_txt_to_Json.py
import json
import os
import glob

def convert_multiple_txt_to_json(input_directory, output_file_path):
    all_data = []
    search_path = os.path.join(input_directory, '*.txt')
    txt_file_paths = glob.glob(search_path)
    
    if not txt_file_paths:
        print(f"Warning: No .txt files were found in the directory '{input_directory}'.")
        return

    print(f"Found {len(txt_file_paths)} .txt files to convert.")
    for file_path in txt_file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as txt_file:
                file_content = txt_file.read()
                data_entry = {"text": file_content}
                all_data.append(data_entry)
                print(f"Successfully processed: {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            # Optional: raise e to stop the process on first error
    
    try:
        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(all_data, json_file, ensure_ascii=False, indent=2)
        print(f"\n✅ Success! All files have been combined into {output_file_path}")
    except Exception as e:
        raise Exception(f"Error writing to JSON file: {e}")