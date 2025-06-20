import argparse
import glob
import os
import sys

def combine_jsonl_files(input_dir, output_file, file_pattern="*.jsonl"):
    """
    Finds all files in a directory matching a pattern, concatenates them
    line by line, and saves them to a single output JSONL file.

    Args:
        input_dir (str): The directory containing the .jsonl files.
        output_file (str): The path for the combined output .jsonl file.
        file_pattern (str): The glob pattern to find files (e.g., '*.jsonl').
    """
    # Create the full search pattern
    search_pattern = os.path.join(input_dir, file_pattern)
    
    # Find all files matching the pattern
    print(f"[*] Searching for files with pattern: {search_pattern}")
    input_files = glob.glob(search_pattern)

    if not input_files:
        print(f"Error: No files found matching '{file_pattern}' in the directory: {input_dir}", file=sys.stderr)
        print("Please check the input directory and pattern.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Found {len(input_files)} files to combine.")

    total_lines_written = 0
    
    try:
        # Open the single output file in write mode
        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Loop through each input file found
            for i, file_path in enumerate(input_files, 1):
                print(f"    ({i}/{len(input_files)}) Processing: {os.path.basename(file_path)}")
                lines_in_file = 0
                # Open the current input file in read mode
                with open(file_path, 'r', encoding='utf-8') as infile:
                    # Read line by line and write to the output file
                    for line in infile:
                        # Ensure the line has content before writing
                        if line.strip():
                            outfile.write(line)
                            lines_in_file += 1
                total_lines_written += lines_in_file

        print("\n[+] Combining complete!")
        print(f"    - Successfully processed {len(input_files)} files.")
        print(f"    - A total of {total_lines_written} lines were written.")
        print(f"    - Combined data saved to: {output_file}")

    except IOError as e:
        print(f"An I/O error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Combine multiple JSONL files from a directory into a single JSONL file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input_directory",
        help="The path to the folder containing the JSONL files to merge."
    )
    parser.add_argument(
        "output_file",
        help="The path for the final merged JSONL file."
    )
    parser.add_argument(
        "--pattern",
        default="*.jsonl",
        help="The file pattern to search for within the input directory."
    )

    args = parser.parse_args()
    
    combine_jsonl_files(args.input_directory, args.output_file, args.pattern)