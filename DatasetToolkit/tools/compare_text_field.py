import json
import os

def load_json(filepath):
    """Loads a JSON file and returns its content. Handles errors."""
    if not os.path.exists(filepath):
        print(f"Error: File not found at '{filepath}'")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading '{filepath}': {e}")
        return None

def main():
    """
    Main function to compare 'text' fields in two JSON lists, 
    reporting both content differences and unmatched items.
    """
    # --- Configuration ---
    file1_path = 'chunk_cache_b11304cf81a6f9b01220f42846080151_size2000.json' 
    file2_path = 'full_stories_list_complete_format.json' 
    output_path = 'text_comparison_report.json' # Renamed for clarity
    # -------------------

    print(f"Comparing '{file1_path}' and '{file2_path}'...")

    json_list1 = load_json(file1_path)
    json_list2 = load_json(file2_path)

    if json_list1 is None or json_list2 is None: return
    if not isinstance(json_list1, list) or not isinstance(json_list2, list):
        print("Error: Both files must contain a JSON list (array).")
        return

    len1, len2 = len(json_list1), len(json_list2)
    comparison_range = min(len1, len2)

    content_differences = []
    unmatched_items = []

    # 1. Compare items that exist in BOTH lists (Content Differences)
    print(f"Comparing the first {comparison_range} items for content differences...")
    for i in range(comparison_range):
        obj1, obj2 = json_list1[i], json_list2[i]
        text1, text2 = obj1.get("text"), obj2.get("text")
        
        if text1 is None or text2 is None:
            print(f"Warning: Skipping index {i} due to missing 'text' field.")
            continue
            
        if text1 != text2:
            content_differences.append({
                "index": i,
                "old_value_file1": text1,
                "new_value_file2": text2
            })

    # 2. Identify items that exist only in the LONGER list (Unmatched Items)
    if len1 != len2:
        print("Identifying unmatched items from the longer list...")
        longer_list = json_list1 if len1 > len2 else json_list2
        source_file = file1_path if len1 > len2 else file2_path

        for i in range(comparison_range, len(longer_list)):
            unmatched_items.append({
                "index": i,
                "source_file": source_file,
                "text_value": longer_list[i].get("text", "N/A")
            })
            
    # 3. Create the final report
    output_data = {
        "summary": {
            "file1": {"path": file1_path, "item_count": len1},
            "file2": {"path": file2_path, "item_count": len2},
            "items_compared_for_content": comparison_range,
            "content_differences_found": len(content_differences),
            "unmatched_items_found": len(unmatched_items)
        },
        "content_differences": content_differences,
        "unmatched_items": unmatched_items
    }
    
    # 4. Write the report to a file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
        print("\n--- Comparison Report ---")
        print(f"Items with different text: {len(content_differences)}")
        print(f"Unmatched items (in longer file): {len(unmatched_items)}")
        print(f"Total differences (content + unmatched): {len(content_differences) + len(unmatched_items)}")
        print(f"Full report saved to '{output_path}'")
    except Exception as e:
        print(f"An error occurred while writing the output file: {e}")

if __name__ == "__main__":
    main()