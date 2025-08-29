# tools/count_tokens.py
import sys
import os
from transformers import AutoTokenizer

def count_tokens_main(input_file: str):
    """
    Counts the tokens in a file using the project's local tokenizer.
    """
    if not input_file or not os.path.exists(input_file):
        print("FATAL: Input file not provided or does not exist.", file=sys.stderr)
        return

    # --- Logic to find the correct tokenizer path ---
    tokenizer_load_path = "meta-llama/Llama-3-8B-Instruct" # Fallback
    try:
        # Check if the script is running in a PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundle_dir = sys._MEIPASS
            local_tokenizer_path = os.path.join(bundle_dir, 'local_tokenizer')
            
            if os.path.isdir(local_tokenizer_path):
                 tokenizer_load_path = local_tokenizer_path
                 print(f"INFO: Running in bundled app. Using local tokenizer.")
            else:
                 print(f"WARNING: Running in bundled app, but local tokenizer folder not found. Falling back to Hub.")
        else:
            # When running as a script, look for the folder in the current project structure
            script_dir = os.path.dirname(__file__)
            proj_root = os.path.abspath(os.path.join(script_dir, '..'))
            local_tokenizer_path = os.path.join(proj_root, 'local_tokenizer')
            if os.path.isdir(local_tokenizer_path):
                tokenizer_load_path = local_tokenizer_path
                print(f"INFO: Running as script. Using local tokenizer from project.")
            else:
                print(f"INFO: Running as script. Local tokenizer not found, falling back to Hub.")

    except Exception as e:
        print(f"WARNING: Could not determine tokenizer path, falling back to Hub. Error: {e}")
    # --- End of tokenizer path logic ---

    print("Loading tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_load_path)
        print(f"Tokenizer '{os.path.basename(tokenizer_load_path)}' loaded successfully.")
    except Exception as e:
        print(f"FATAL: Could not load tokenizer from '{tokenizer_load_path}'. Error: {e}", file=sys.stderr)
        raise

    print(f"\nReading content from: {os.path.basename(input_file)}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"FATAL: Error reading file: {e}", file=sys.stderr)
        return

    # Calculate and print the number of tokens
    tokens = tokenizer.encode(content)
    token_count = len(tokens)
    
    print("-" * 20)
    print(f"File:         {os.path.basename(input_file)}")
    print(f"Token Count:  {token_count:,}")
    print("-" * 20)

if __name__ == '__main__':
    # This part allows the script to be run directly for testing
    if len(sys.argv) != 2:
        print("Usage: python count_tokens.py <path_to_file>")
        sys.exit(1)
    count_tokens_main(sys.argv[1])