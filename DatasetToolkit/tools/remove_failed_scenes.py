import json
import argparse
import sys
from pathlib import Path

# The specific phrase to detect for removing a JSONL entry.
FAILED_SCENE_PHRASE = "[Scene description generation failed due to API errors.]"

def remove_failed_scenes_main(input_file: str, output_file: str):
    """
    Reads a JSONL file, removes lines containing a specific failure phrase,
    and writes the clean lines to a new file.

    Args:
        input_file (str): Path to the input JSONL file.
        output_file (str): Path to the output JSONL file.
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.is_file():
        error_msg = f"Error: Input file not found at {input_path}"
        print(error_msg, file=sys.stderr)
        raise FileNotFoundError(error_msg)

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines_read = 0
    lines_written = 0
    lines_removed = 0

    print(f"Starting to process {input_path.name}...")
    print(f"Searching for and removing lines containing: '{FAILED_SCENE_PHRASE}'")

    try:
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for i, line in enumerate(infile, 1):
                lines_read = i
                # Check for the phrase in the raw line for efficiency.
                # This avoids unnecessary JSON parsing if the phrase is present.
                if FAILED_SCENE_PHRASE in line:
                    lines_removed += 1
                    continue  # Skip this line and move to the next

                # Optional but recommended: Validate if the line is valid JSON before writing.
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping malformed JSON on line {lines_read}: {line.strip()}", file=sys.stderr)
                    lines_removed += 1
                    continue

                outfile.write(line)
                lines_written += 1

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        raise

    print("\nProcessing complete.")
    print(f"Total lines read: {lines_read}")
    print(f"Lines written to output: {lines_written}")
    print(f"Lines removed (contained phrase or were malformed): {lines_removed}")
    print(f"Cleaned file saved to: {output_path}")

def main():
    """Command-line interface for the script."""
    parser = argparse.ArgumentParser(
        description="Removes entries from a JSONL file that contain the phrase "
                    "'[Scene description generation failed due to API errors.]'."
    )
    parser.add_argument(
        "-i", "--input_file",
        required=True,
        help="Path to the input JSONL file."
    )
    parser.add_argument(
        "-o", "--output_file",
        required=True,
        help="Path to the output JSONL file."
    )
    args = parser.parse_args()

    remove_failed_scenes_main(args.input_file, args.output_file)

if __name__ == '__main__':
    main()