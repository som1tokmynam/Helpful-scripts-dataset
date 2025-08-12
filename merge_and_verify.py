import torch
from transformers import AutoTokenizer, AutoConfig, AutoModelForCausalLM
from peft import LoraConfig
import safetensors.torch
import os
import shutil
from tqdm import tqdm
import json
import sys
import argparse

# ===================================================================================
# ---                           CONFIGURATION                                     ---
# ===================================================================================
test_messages = [
    {
        "role": "system",
        "content": (
            "You are a creative and helpful assistant who acts as a game master for a fantasy role-playing game. "
            "When you are asked to provide a list of options or choices for the player, you MUST enclose the entire list "
            "within <choices> and </choices> tags."
        )
    },
    {
        "role": "user",
        "content": (
            "The hero stands before a sealed, ancient door humming with magical energy. What are her three possible courses of action? "
            "Please provide these as choices."
        )
    }
]
# ===================================================================================

def load_vocab_tensors_safely(path, tokenizer_vocab_size):
    """Load and validate vocabulary tensors, expanding if necessary."""
    print(f"Attempting to load vocabulary tensors from: {path}")

    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return None, None

    # Try to load adapter files
    adapter_file = os.path.join(path, 'adapter_model.safetensors')
    if not os.path.exists(adapter_file):
        adapter_file = os.path.join(path, 'adapter_model.bin')

    if not os.path.exists(adapter_file):
        print(f"No adapter file found in {path}")
        return None, None

    print(f"Loading from: {adapter_file}")
    try:
        if adapter_file.endswith(".bin"):
            state_dict = torch.load(adapter_file, map_location="cpu")
        else:
            state_dict = safetensors.torch.load_file(adapter_file, device="cpu")
    except Exception as e:
        print(f"Failed to load adapter file: {e}")
        return None, None

    # Look for vocab tensors with various possible keys
    possible_embed_keys = [
        "base_model.model.model.embed_tokens.weight",
        "model.embed_tokens.weight",
        "base_model.model.embed_tokens.weight",
        "embed_tokens.weight"
    ]
    possible_lm_head_keys = [
        "base_model.model.lm_head.weight",
        "lm_head.weight",
        "base_model.lm_head.weight"
    ]

    embed_tensor = None
    lm_head_tensor = None

    for key in possible_embed_keys:
        if key in state_dict:
            embed_tensor = state_dict[key]
            print(f"Found embed tensor with key: {key}, shape: {embed_tensor.shape}")
            break

    for key in possible_lm_head_keys:
        if key in state_dict:
            lm_head_tensor = state_dict[key]
            print(f"Found lm_head tensor with key: {key}, shape: {lm_head_tensor.shape}")
            break

    # Validate tensor sizes
    if embed_tensor is not None:
        actual_vocab_size = embed_tensor.shape[0]
        if actual_vocab_size != tokenizer_vocab_size:
            print(f"WARNING: Embed tensor vocab size ({actual_vocab_size}) != tokenizer vocab size ({tokenizer_vocab_size})")
            if actual_vocab_size < tokenizer_vocab_size:
                print("Expanding embed tensor to match tokenizer...")
                # Expand with random initialization for new tokens
                embed_dim = embed_tensor.shape[1]
                expanded_embed = torch.zeros(tokenizer_vocab_size, embed_dim, dtype=embed_tensor.dtype)
                expanded_embed[:actual_vocab_size] = embed_tensor
                # Initialize new tokens with small random values
                if tokenizer_vocab_size > actual_vocab_size:
                    torch.nn.init.normal_(expanded_embed[actual_vocab_size:], mean=0.0, std=0.02)
                embed_tensor = expanded_embed
                print(f"Expanded embed tensor to shape: {embed_tensor.shape}")

    if lm_head_tensor is not None:
        actual_vocab_size = lm_head_tensor.shape[0]
        if actual_vocab_size != tokenizer_vocab_size:
            print(f"WARNING: LM head tensor vocab size ({actual_vocab_size}) != tokenizer vocab size ({tokenizer_vocab_size})")
            if actual_vocab_size < tokenizer_vocab_size:
                print("Expanding lm_head tensor to match tokenizer...")

                if embed_tensor is None or len(embed_tensor.shape) != 2:
                    print("ERROR: Cannot expand lm_head tensor. A valid 2D embed_tensor is required to infer dimensions.")
                    return embed_tensor, None

                lm_head_dim = embed_tensor.shape[1]
                target_dtype = embed_tensor.dtype
                print(f"Inferred lm_head hidden dim ({lm_head_dim}) and dtype ({target_dtype}) from embed tensor.")

                expanded_lm_head = torch.zeros(tokenizer_vocab_size, lm_head_dim, dtype=target_dtype)

                if actual_vocab_size > 0:
                    expanded_lm_head[:actual_vocab_size] = lm_head_tensor

                if tokenizer_vocab_size > actual_vocab_size:
                    torch.nn.init.normal_(expanded_lm_head[actual_vocab_size:], mean=0.0, std=0.02)

                lm_head_tensor = expanded_lm_head
                print(f"Expanded lm_head tensor to shape: {lm_head_tensor.shape}")

    return embed_tensor, lm_head_tensor

def get_base_model_vocab_tensors(base_model_path):
    """Extract original vocab tensors from base model for fallback."""
    print("Loading base model vocabulary tensors as fallback...")

    base_model_index_path = os.path.join(base_model_path, "model.safetensors.index.json")
    with open(base_model_index_path, 'r') as f:
        base_model_index = json.load(f)
    weight_map = base_model_index["weight_map"]

    embed_tensor = None
    lm_head_tensor = None

    embed_shard = weight_map.get("model.embed_tokens.weight")
    lm_head_shard = weight_map.get("lm_head.weight")

    if embed_shard:
        shard_path = os.path.join(base_model_path, embed_shard)
        shard = safetensors.torch.load_file(shard_path, device="cpu")
        embed_tensor = shard.get("model.embed_tokens.weight")
        if embed_tensor is not None:
            print(f"Loaded base embed tensor, shape: {embed_tensor.shape}")

    if lm_head_shard:
        shard_path = os.path.join(base_model_path, lm_head_shard)
        shard = safetensors.torch.load_file(shard_path, device="cpu")
        lm_head_tensor = shard.get("lm_head.weight")
        if lm_head_tensor is not None:
            print(f"Loaded base lm_head tensor, shape: {lm_head_tensor.shape}")

    return embed_tensor, lm_head_tensor

def expand_vocab_tensor(tensor, current_vocab_size, new_vocab_size, tensor_name):
    """Expand a vocabulary tensor to match the new vocabulary size."""
    if tensor is None:
        print(f"ERROR: Cannot expand {tensor_name} - tensor is None")
        return None

    if current_vocab_size >= new_vocab_size:
        print(f"{tensor_name} already has sufficient size ({current_vocab_size} >= {new_vocab_size})")
        return tensor

    print(f"Expanding {tensor_name} from {current_vocab_size} to {new_vocab_size}")

    if len(tensor.shape) != 2:
        print(f"ERROR: Expected 2D tensor for {tensor_name}, got shape {tensor.shape}")
        return None

    hidden_dim = tensor.shape[1]
    expanded_tensor = torch.zeros(new_vocab_size, hidden_dim, dtype=tensor.dtype)

    expanded_tensor[:current_vocab_size] = tensor

    if new_vocab_size > current_vocab_size:
        torch.nn.init.normal_(expanded_tensor[current_vocab_size:], mean=0.0, std=0.02)
        print(f"Initialized {new_vocab_size - current_vocab_size} new tokens with random values")

    print(f"Expanded {tensor_name} to shape: {expanded_tensor.shape}")
    return expanded_tensor

def do_merge(base_model_path, lora_path, final_lora_path, output_path):
    """Performs the full, robust, hybrid merge."""
    print("Starting HYBRID LoRA merge process (v-FINAL - with vocab expansion fix)...")
    os.makedirs(output_path, exist_ok=True)

    # 1. Config and Tokenizer Setup
    print("\n--- 1. Setting up Config and Tokenizer ---")
    tokenizer = AutoTokenizer.from_pretrained(lora_path)
    config = AutoConfig.from_pretrained(base_model_path)
    new_vocab_size = len(tokenizer)
    original_vocab_size = config.vocab_size
    print(f"Tokenizer vocabulary size: {new_vocab_size}")
    print(f"Original config vocabulary size: {original_vocab_size}")

    vocab_expanded = False
    if new_vocab_size > config.vocab_size:
        print(f"Vocabulary expanded from {config.vocab_size} to {new_vocab_size}.")
        config.vocab_size = new_vocab_size
        vocab_expanded = True
    config.save_pretrained(output_path)

    for filename in ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "tokenizer.model"]:
        if os.path.exists(os.path.join(lora_path, filename)):
            shutil.copy(os.path.join(lora_path, filename), output_path)

    # 2. Inject Chat Template
    print("\n--- 2. Injecting Chat Template ---")
    tokenizer_config_path = os.path.join(output_path, 'tokenizer_config.json')
    if os.path.exists(tokenizer_config_path):
        with open(tokenizer_config_path, 'r+') as f:
            tokenizer_config = json.load(f)
            if 'chat_template' not in tokenizer_config:
                print("Injecting missing chat template into tokenizer_config.json...")
                chat_template = "{%- set today = strftime_now(\"%Y-%m-%d\") %}{%- set default_system_message = \"You are Mistral Small 3, a Large Language Model (LLM) created by Mistral AI, a French startup headquartered in Paris.\\nYour knowledge base was last updated on 2023-10-01. The current date is \" + today + \".\\n\\nWhen you're not sure about some information, you say that you don't have the information and don't make up anything.\\nIf the user's question is not clear, ambiguous, or does not provide enough context for you to accurately answer the question, you do not try to answer it right away and you rather ask the user to clarify their request (e.g. \\\"What are some good restaurants around me?\\\")\" %}{{ bos_token }}{%- if messages[0]['role'] == 'system' %}{%- if messages[0]['content'] is string %}{%- set system_message = messages[0]['content'] %}{%- else %}{%- set system_message = messages[0]['content'][0]['text'] %}{%- endif %}{%- set loop_messages = messages[1:] %}{%- else %}{%- set system_message = default_system_message %}{%- set loop_messages = messages %}{%- endif %}{{- '[SYSTEM_PROMPT]' + system_message + '[/SYSTEM_PROMPT]' }}{%- for message in loop_messages %}{%- if message['role'] == 'user' %}{%- if message['content'] is string %}{{- '[INST]' + message['content'] + '[/INST]' }}{%- else %}{{- '[INST]' }}{%- for block in message['content'] %}{%- if block['type'] == 'text' %}{{- block['text'] }}{%- elif block['type'] in ['image', 'image_url'] %}{{- '[IMG]' }}{%- else %}{{- raise_exception('Only text and image blocks are supported in message content!') }}{%- endif %}{%- endfor %}{{- '[/INST]' }}{%- endif %}{%- elif message['role'] == 'system' %}{%- if message['content'] is string %}{{- '[SYSTEM_PROMPT]' + message['content'] + '[/SYSTEM_PROMPT]' }}{%- else %}{{- '[SYSTEM_PROMPT]' + message['content'][0]['text'] + '[/SYSTEM_PROMPT]' }}{%- endif %}{%- elif message['role'] == 'assistant' %}{%- if message['content'] is string %}{{- message['content'] + eos_token }}{%- else %}{{- message['content'][0]['text'] + eos_token }}{%- endif %}{%- else %}{{- raise_exception('Only user, system and assistant roles are supported!') }}{%- endif %}{%- endfor %}"
                tokenizer_config['chat_template'] = chat_template
                f.seek(0)
                json.dump(tokenizer_config, f, indent=2)
                f.truncate()
            else:
                print("Chat template already exists.")

    # 3. Load LoRA Weights
    print("\n--- 3. Loading LoRA Weights ---")
    lora_config = LoraConfig.from_json_file(os.path.join(lora_path, 'adapter_config.json'))
    lora_adapter_file = os.path.join(lora_path, 'adapter_model.safetensors')
    if not os.path.exists(lora_adapter_file):
        lora_adapter_file = os.path.join(lora_path, 'adapter_model.bin')

    print(f"Loading primary delta weights from: {lora_adapter_file}")
    if lora_adapter_file.endswith(".bin"):
        lora_state_dict = torch.load(lora_adapter_file, map_location="cpu")
    else:
        lora_state_dict = safetensors.torch.load_file(lora_adapter_file, device="cpu")

    # 4. Handle Vocabulary Tensors with Smart Fallback
    print("\n--- 4. Loading Vocabulary Tensors ---")

    embed_tensor = None
    lm_head_tensor = None

    # If --final is provided, it's the primary source for vocabulary tensors.
    if final_lora_path:
        print(f"Attempting to load vocabulary from --final path: {final_lora_path}")
        embed_tensor, lm_head_tensor = load_vocab_tensors_safely(final_lora_path, new_vocab_size)
    else:
        # This is a standard merge without a separate vocabulary source.
        # Tensors remain None, which will trigger the fallback logic.
        print("Standard merge: No --final path provided. Will use base model's vocabulary.")

    # Fallback Logic: If tensors were not loaded from --final (or it wasn't provided),
    # use the base model's vocabulary as the source.
    if embed_tensor is None or lm_head_tensor is None:
        if final_lora_path: # Only print this if we tried to load from --final and failed
            print("\nWARNING: --final path did not contain complete vocabulary tensors. Falling back to base model.")
        
        print("Loading base model vocabulary as a fallback source...")
        base_embed, base_lm_head = get_base_model_vocab_tensors(base_model_path)

        # Use base embed tensor if we don't have one yet
        if embed_tensor is None and base_embed is not None:
            print("Using base model's embed_tokens tensor.")
            if vocab_expanded:
                embed_tensor = expand_vocab_tensor(base_embed, original_vocab_size, new_vocab_size, "embed_tokens")
            else:
                embed_tensor = base_embed

        # Use base lm_head tensor if we don't have one yet
        if lm_head_tensor is None and base_lm_head is not None:
            print("Using base model's lm_head tensor.")
            if vocab_expanded:
                lm_head_tensor = expand_vocab_tensor(base_lm_head, original_vocab_size, new_vocab_size, "lm_head")
            else:
                lm_head_tensor = base_lm_head

    if embed_tensor is None or lm_head_tensor is None:
        print("ERROR: Could not obtain valid vocabulary tensors!")
        if embed_tensor is None: print("  - embed_tensor is None")
        if lm_head_tensor is None: print("  - lm_head_tensor is None")
        sys.exit(1)

    if embed_tensor.shape[0] != new_vocab_size:
        print(f"ERROR: embed_tensor vocab size ({embed_tensor.shape[0]}) != expected ({new_vocab_size})")
        sys.exit(1)

    if lm_head_tensor.shape[0] != new_vocab_size:
        print(f"ERROR: lm_head_tensor vocab size ({lm_head_tensor.shape[0]}) != expected ({new_vocab_size})")
        sys.exit(1)

    print(f"✓ Final embed tensor shape: {embed_tensor.shape}")
    print(f"✓ Final lm_head tensor shape: {lm_head_tensor.shape}")
    print(f"✓ Expected vocab size: {new_vocab_size}")

    # 5. Load Base Model Index
    print("\n--- 5. Loading Base Model Index ---")
    base_model_index_path = os.path.join(base_model_path, "model.safetensors.index.json")
    with open(base_model_index_path, 'r') as f:
        base_model_index = json.load(f)
    weight_map = base_model_index["weight_map"]

    # 6. Merge LoRA Deltas
    print("\n--- 6. Merging LoRA Deltas into Shards ---")
    base_model_shards = sorted(list(set(weight_map.values())))

    vocab_shards = set()
    if "model.embed_tokens.weight" in weight_map: vocab_shards.add(weight_map["model.embed_tokens.weight"])
    if "lm_head.weight" in weight_map: vocab_shards.add(weight_map["lm_head.weight"])

    for shard_name in tqdm(base_model_shards, desc="Merging LoRA into shards"):
        shard_path = os.path.join(base_model_path, shard_name)
        shard = safetensors.torch.load_file(shard_path, device="cpu")
        new_shard = {}

        for key, tensor in shard.items():
            if key not in ["model.embed_tokens.weight", "lm_head.weight"]:
                new_shard[key] = tensor

        keys_to_merge = [k for k in new_shard.keys() if f"base_model.model.{k}.lora_A.weight" in lora_state_dict]
        for key in keys_to_merge:
            lora_A = lora_state_dict[f"base_model.model.{key}.lora_A.weight"]
            lora_B = lora_state_dict[f"base_model.model.{key}.lora_B.weight"]
            scaling = lora_config.lora_alpha / lora_config.r
            original_tensor = new_shard[key]
            new_shard[key] = (original_tensor.to(torch.float32) + (lora_B.to(torch.float32) @ lora_A.to(torch.float32)) * scaling).to(original_tensor.dtype)

        if new_shard:
            output_shard_path = os.path.join(output_path, shard_name)
            safetensors.torch.save_file(new_shard, output_shard_path, metadata={'format': 'pt'})

    # 7. Handle Vocab Expansion
    print("\n--- 7. Saving Vocabulary Tensors ---")
    new_tensors = {
        "model.embed_tokens.weight": embed_tensor,
        "lm_head.weight": lm_head_tensor
    }

    new_shard_num = max([int(f.split('-')[1]) for f in base_model_shards]) + 1
    total_shards = len(base_model_shards) + 1
    new_shard_name = f"model-{new_shard_num:05d}-of-{total_shards:05d}.safetensors"
    print(f"Saving vocabulary tensors to new shard: {new_shard_name}")
    safetensors.torch.save_file(new_tensors, os.path.join(output_path, new_shard_name), metadata={'format': 'pt'})

    # 8. Create and save the final, cleaned index file
    print("\n--- 8. Finalizing Model Index (with cleaning) ---")
    final_weight_map = {}

    for key, shard in weight_map.items():
        if key not in ["model.embed_tokens.weight", "lm_head.weight"]:
            final_weight_map[key] = shard

    for key in new_tensors.keys():
        print(f"Adding new mapping to index: '{key}' -> '{new_shard_name}'")
        final_weight_map[key] = new_shard_name

    final_index_data = {
        "metadata": base_model_index.get("metadata", {}),
        "weight_map": final_weight_map
    }
    index_file_path = os.path.join(output_path, "model.safetensors.index.json")
    with open(index_file_path, 'w') as f:
        json.dump(final_index_data, f, indent=2)

    print(f"\nSuccessfully created cleaned safetensors index file at: {index_file_path}")
    print("\nMERGE PROCESS COMPLETED SUCCESSFULLY!")

def do_verify(output_path, test_messages):
    """Performs a full verification of the merged model."""
    print("\n\n=========================================================")
    print("---      STARTING AUTOMATIC VERIFICATION            ---")
    print("=========================================================")

    # 1. Structural Integrity Test
    print("\n--- 1. STRUCTURAL INTEGRITY TEST (LOADING) ---")
    try:
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(output_path)
        print("Tokenizer loaded successfully.")
        if tokenizer.chat_template is None:
            print("\n[FATAL] Tokenizer loaded, but is MISSING the 'chat_template'.")
            sys.exit(1)
        print("Found a valid chat template in the tokenizer's configuration.")

        print("Loading model...")
        model = AutoModelForCausalLM.from_pretrained(
            output_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        print("\n[SUCCESS] Model loaded successfully onto memory/GPU(s)!")

    except Exception as e:
        print(f"\n[FATAL FAILURE] An error occurred while loading the model.")
        print("This is likely a 'size mismatch' error.")
        print(f"Details: {e}")
        sys.exit(1)

    # 2. Fidelity & Vocabulary Test
    print("\n--- 2. FIDELITY & VOCABULARY TEST ---")
    print("Applying chat template to test messages...")
    final_prompt_string = tokenizer.apply_chat_template(
        test_messages,
        tokenize=False,
        add_generation_prompt=True
    )
    print("\nFinal prompt string generated by tokenizer:")
    print("---------------------------------")
    print(final_prompt_string)
    print("---------------------------------")

    inputs_fidelity = tokenizer(final_prompt_string, return_tensors="pt").to(model.device)
    outputs_fidelity = model.generate(**inputs_fidelity, max_new_tokens=250, do_sample=True, top_p=0.9, temperature=0.7)
    decoded_fidelity = tokenizer.decode(outputs_fidelity[0], skip_special_tokens=False)

    print("\nModel Fidelity Response:")
    print(decoded_fidelity)

    print("\n--- Verification Complete ---")
    print("If the text above is coherent and uses the <choices> tags, your model is PERFECT.")


if __name__ == "__main__":
    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(description="Hybrid LoRA merge script with vocabulary expansion.")

    # Required arguments
    parser.add_argument("--base", type=str, required=True,
                        help="Path to the base model directory.")
    parser.add_argument("--lora", type=str, required=True,
                        help="Path to the primary LoRA adapter directory (the one with the delta weights).")
    parser.add_argument("--out", type=str, required=True,
                        help="Path to the output directory for the merged model.")
    
    # Optional argument for final vocabulary
    parser.add_argument("--final", type=str, required=False, default=None,
                        help="Optional: Path to the LoRA adapter with the final vocab/tokenizer. "
                             "If not provided, a standard merge is performed using the base model's vocabulary.")

    # Parse the arguments provided by the user
    args = parser.parse_args()

    # Call the merge function with arguments from the command line
    do_merge(
        base_model_path=args.base,
        lora_path=args.lora,
        final_lora_path=args.final,  # This will be None if the arg is not passed
        output_path=args.out
    )
    
    # Call the verification function with the output path
    do_verify(
        output_path=args.out,
        test_messages=test_messages
    )
