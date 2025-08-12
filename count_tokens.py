import sys
import argparse
import tiktoken

def count_tokens(text: str, encoding_name: str) -> int:
    """Counts the number of tokens in a text string using the specified encoding."""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
    except ValueError:
        print(f"Error: Encoding '{encoding_name}' not found.")
        print("Available encodings: ", tiktoken.list_encoding_names())
        sys.exit(1)
        
    token_integers = encoding.encode(text)
    return len(token_integers)

def main():
    """Main function to parse arguments and count tokens."""
    parser = argparse.ArgumentParser(
        description="Calculate the number of tokens in a file or from stdin.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
        help="The file to process. Reads from stdin if not provided."
    )
    parser.add_argument(
        "-e", "--encoding",
        default="cl100k_base",
        help=(
            "The encoding to use. Defaults to 'cl100k_base'.\n"
            "'cl100k_base' is used by gpt-4, gpt-3.5-turbo, text-embedding-ada-002.\n"
            "'p50k_base' is used by older models like text-davinci-003."
        )
    )

    args = parser.parse_args()

    # Read text from file or stdin
    try:
        content = args.file.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Close the file if it's not stdin
        if args.file is not sys.stdin:
            args.file.close()

    # Calculate and print the number of tokens
    token_count = count_tokens(content, args.encoding)
    print(f"Encoding: {args.encoding}")
    print(f"Token count: {token_count:,}")


if __name__ == "__main__":
    main()