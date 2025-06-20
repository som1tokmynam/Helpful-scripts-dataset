import json
import argparse
import sys

def convert_json_to_jsonl(input_path, output_path):
    """
    Converts a JSON file to a JSON Lines file.

    The input JSON file can contain either a single JSON object or a list of
    JSON objects.

    Args:
        input_path (str): Path to the input .json file.
        output_path (str): Path to the output .jsonl file.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f_in:
            data = json.load(f_in)

        with open(output_path, 'w', encoding='utf-8') as f_out:
            if isinstance(data, list):
                # If the JSON file contains a list of objects
                total_objects = len(data)
                print(f"Input is a list containing {total_objects} objects.")
                for i, obj in enumerate(data):
                    # Ensure each object is converted to a string before writing
                    json_record = json.dumps(obj, ensure_ascii=False)
                    f_out.write(json_record + '\n')
                print(f"Successfully converted {total_objects} objects.")

            elif isinstance(data, dict):
                # If the JSON file contains a single object
                print("Input is a single JSON object.")
                json_record = json.dumps(data, ensure_ascii=False)
                f_out.write(json_record + '\n')
                print("Successfully converted 1 object.")

            else:
                print(f"Error: Unsupported JSON structure in {input_path}. "
                      "Only a list of objects or a single object is supported.", file=sys.stderr)
                sys.exit(1)

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{input_path}'. "
              "Please ensure it is a valid JSON file.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nConversion complete. Output saved to '{output_path}'")

if __name__ == "__main__":
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Convert a .json file to a .jsonl file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_file",
        help="The path to the input .json file."
    )
    parser.add_argument(
        "output_file",
        help="The path for the output .jsonl file."
    )

    args = parser.parse_args()

    # Call the conversion function
    convert_json_to_jsonl(args.input_file, args.output_file)