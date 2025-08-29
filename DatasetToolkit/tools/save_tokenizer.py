# save_tokenizer.py
from transformers import AutoTokenizer

# Use the non-gated model to download the files
MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct"
OUTPUT_DIR = "local_tokenizer"

print(f"Downloading tokenizer for '{MODEL_NAME}'...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print(f"Saving tokenizer files to '{OUTPUT_DIR}'...")
tokenizer.save_pretrained(OUTPUT_DIR)

print("Done.")