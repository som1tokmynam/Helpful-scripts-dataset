import torch
import safetensors.torch
from transformers import AutoTokenizer, AutoConfig
from peft import LoraConfig
import os
import shutil
from tqdm import tqdm
import json

# --- Configuration ---
# You can point this script at either type of LoRA adapter
base_model_path = "/media/administrator/oiseauxai1data/modelweights/M3.2-36B-Instruct"
lora_path = "/media/administrator/oiseauxai1data/checkpoint-306"
output_path = "/media/administrator/oiseauxai1data/modelweights/M3.2-36B-Animus-V8.1"
# --- End Configuration ---

print("Starting ROBUST LoRA merge process for sharded models...")
os.makedirs(output_path, exist_ok=True)

# 1. Load tokenizer and config from LoRA, update vocab size
print("--- 1. Loading Tokenizer & Config ---")
tokenizer = AutoTokenizer.from_pretrained(lora_path)
new_vocab_size = len(tokenizer)

base_config = AutoConfig.from_pretrained(base_model_path)
original_vocab_size = base_config.vocab_size

if new_vocab_size > original_vocab_size:
    print(f"Vocabulary expanded from {original_vocab_size} to {new_vocab_size}.")
    base_config.vocab_size = new_vocab_size
else:
    print(f"Vocabulary size unchanged: {original_vocab_size}")

base_config.save_pretrained(output_path)
print(f"Saved updated config.json to {output_path}")

# 2. Copy all tokenizer files
print("\n--- 2. Copying Tokenizer Files ---")
for filename in ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "tokenizer.model"]:
    if os.path.exists(os.path.join(lora_path, filename)):
        shutil.copy(os.path.join(lora_path, filename), output_path)
        print(f"Copied {filename}")

# 3. Load LoRA config and weights
print("\n--- 3. Loading LoRA Adapter ---")
lora_config = LoraConfig.from_json_file(os.path.join(lora_path, 'adapter_config.json'))
lora_adapter_file = os.path.join(lora_path, 'adapter_model.safetensors')
if not os.path.exists(lora_adapter_file):
    lora_adapter_file = os.path.join(lora_path, 'adapter_model.bin')

print(f"Loading adapter weights from: {lora_adapter_file}")
lora_state_dict = torch.load(lora_adapter_file, map_location="cpu") if lora_adapter_file.endswith(".bin") else safetensors.torch.load_file(lora_adapter_file, device="cpu")

# Find and extract the full tensors, removing them from the LoRA dict
possible_embed_keys = ["model.embed_tokens.weight", "base_model.model.model.embed_tokens.weight", "base_model.model.embed_tokens.weight"]
possible_lm_head_keys = ["lm_head.weight", "base_model.model.lm_head.weight"]
embed_tensor_key = next((key for key in possible_embed_keys if key in lora_state_dict), None)
lm_head_tensor_key = next((key for key in possible_lm_head_keys if key in lora_state_dict), None)

embed_tensor = lora_state_dict.pop(embed_tensor_key, None)
lm_head_tensor = lora_state_dict.pop(lm_head_tensor_key, None)

# --- 3a. Analyze Full Tensors from Adapter (NEW DEBUGGING SECTION) ---
print("\n--- 3a. Analyzing Full Tensors from Adapter ---")
print(f"Tokenizer vocabulary size: {new_vocab_size}")

if embed_tensor is not None:
    lora_embed_vocab_size = embed_tensor.shape[0]
    print(f"Found 'embed_tokens' tensor in adapter with key: '{embed_tensor_key}'")
    print(f"  - Adapter's embedding tensor vocab size: {lora_embed_vocab_size}")
    if lora_embed_vocab_size != new_vocab_size:
        print(f"\n  [!!! WARNING !!!]")
        print(f"  - Mismatch detected: Adapter vocab size ({lora_embed_vocab_size}) != Tokenizer vocab size ({new_vocab_size}).")
        print(f"  - The script will proceed, but this may result in a corrupt model.")
        print(f"  - Please ensure you're using the tokenizer that was saved with this specific LoRA adapter.\n")
else:
    print("Did not find a full 'embed_tokens' tensor in the adapter.")
    print("  - This is normal if you did not use 'lora_modules_to_save' for embeddings.")

if lm_head_tensor is not None:
    lora_lm_head_vocab_size = lm_head_tensor.shape[0]
    print(f"Found 'lm_head' tensor in adapter with key: '{lm_head_tensor_key}'")
    print(f"  - Adapter's lm_head tensor vocab size: {lora_lm_head_vocab_size}")
    if lora_lm_head_vocab_size != new_vocab_size:
        print(f"\n  [!!! WARNING !!!]")
        print(f"  - Mismatch detected: Adapter vocab size ({lora_lm_head_vocab_size}) != Tokenizer vocab size ({new_vocab_size}).\n")
else:
    print("Did not find a full 'lm_head' tensor in the adapter.")
    print("  - This is normal if you did not use 'lora_modules_to_save' for the lm_head.")

# 4. Load the original model's index and create the initial weight map
print("\n--- 4. Loading Base Model Index ---")
base_model_index_path = os.path.join(base_model_path, "model.safetensors.index.json")
with open(base_model_index_path, 'r') as f:
    base_model_index = json.load(f)
weight_map = base_model_index["weight_map"]
print("Loaded base model weight map.")

# 5. Merge LoRA weights into base model shards
print("\n--- 5. Merging LoRA Deltas into Shards ---")
base_model_shards = set(weight_map.values())
for shard_name in tqdm(base_model_shards, desc="Merging LoRA into shards"):
    shard_path = os.path.join(base_model_path, shard_name)
    shard = safetensors.torch.load_file(shard_path, device="cpu")
    new_shard = shard.copy()

    keys_to_merge = [k for k in shard.keys() if f"base_model.model.{k}.lora_A.weight" in lora_state_dict]

    for key in keys_to_merge:
        original_tensor = shard[key]
        lora_A = lora_state_dict[f"base_model.model.{key}.lora_A.weight"]
        lora_B = lora_state_dict[f"base_model.model.{key}.lora_B.weight"]
        scaling = lora_config.lora_alpha / lora_config.r
        
        merged_tensor = original_tensor.to(torch.float32) + (lora_B.to(torch.float32) @ lora_A.to(torch.float32)) * scaling
        new_shard[key] = merged_tensor.to(original_tensor.dtype)

    output_shard_path = os.path.join(output_path, shard_name)
    safetensors.torch.save_file(new_shard, output_shard_path, metadata={'format': 'pt'})

# 6. Handle the full tensors (embed and lm_head) by saving to a new shard
print("\n--- 6. Handling Full Tensors (e.g., Vocab Expansion) ---")
new_tensors = {}
if embed_tensor is not None:
    if embed_tensor.shape[0] == new_vocab_size:
        print("Embed tensor matches new vocab size. Staging for new shard.")
        new_tensors["model.embed_tokens.weight"] = embed_tensor
    else:
        print("[WARNING] Embed tensor in adapter has a mismatched size. SKIPPING its inclusion.")

if lm_head_tensor is not None:
    if lm_head_tensor.shape[0] == new_vocab_size:
        print("LM head tensor matches new vocab size. Staging for new shard.")
        new_tensors["lm_head.weight"] = lm_head_tensor
    else:
        print("[WARNING] LM head tensor in adapter has a mismatched size. SKIPPING its inclusion.")

if new_tensors:
    existing_shard_nums = [int(f.split('-')[1]) for f in base_model_shards]
    new_shard_num = max(existing_shard_nums) + 1
    total_shards = len(base_model_shards) + 1
    new_shard_name = f"model-{new_shard_num:05d}-of-{total_shards:05d}.safetensors"
    
    print(f"Saving new vocabulary tensors to a new shard: {new_shard_name}")
    new_shard_path = os.path.join(output_path, new_shard_name)
    safetensors.torch.save_file(new_tensors, new_shard_path, metadata={'format': 'pt'})
    
    for key in new_tensors.keys():
        weight_map[key] = new_shard_name
        print(f"Updated weight map: '{key}' -> '{new_shard_name}'")
else:
    print("No new full tensors to save to a separate shard.")

# 7. Create and save the final index file
print("\n--- 7. Finalizing Model Index ---")
final_index_data = {
    "metadata": base_model_index.get("metadata", {}),
    "weight_map": weight_map
}

index_file_path = os.path.join(output_path, "model.safetensors.index.json")
with open(index_file_path, 'w') as f:
    json.dump(final_index_data, f, indent=2)

print(f"\nSuccessfully created safetensors index file at: {index_file_path}")
print("\nRobust merge process completed successfully!")
print(f"Final merged model saved to: {output_path}")