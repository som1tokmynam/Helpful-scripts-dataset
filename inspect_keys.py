# inspect_keys.py
import safetensors.torch
import sys

# --- Configuration ---
# You can either set the path here or provide it as a command line argument
# Example: python inspect_keys.py /path/to/your/adapter_model.safetensors
safetensors_file_path = "/media/administrator/oiseauxai1data/checkpoint-408/adapter_model.safetensors"
# --- End Configuration ---

if len(sys.argv) > 1:
    safetensors_file_path = sys.argv[1]

print(f"--- Inspecting Keys in: {safetensors_file_path} ---")

try:
    state_dict = safetensors.torch.load_file(safetensors_file_path)
except Exception as e:
    print(f"Error loading file: {e}")
    sys.exit(1)

print(f"Found {len(state_dict)} total tensors. Listing all keys:\n")

# Find the longest key for alignment
max_len = 0
if state_dict.keys():
    max_len = max(len(k) for k in state_dict.keys())

for key in sorted(state_dict.keys()):
    # We'll highlight the keys we're interested in
    if 'embed' in key or 'lm_head' in key:
        print(f"*** {key.ljust(max_len)} <-- LIKELY CANDIDATE")
    else:
        # To avoid a massive wall of text, you can comment out the next line
        # if you only want to see the candidate keys.
        print(f"    {key}")

print("\n--- Inspection Complete ---")
print("Look for the highlighted keys. You will need to copy the EXACT key names into the merge script.")