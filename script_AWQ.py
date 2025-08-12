import torch
import os
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer
from datasets import load_dataset

# Step 1: Configuration
# ----------------------
model_path = "Darkhn/L3.3-70B-Animus-V4-Final"
quant_path = "./output/L3.3-70B-Animus-V4-Final-AWQ"
quant_config = { "zero_point": True, "q_group_size": 128, "w_bit": 4, "version": "GEMM" }
max_memory = {0: "70GIB", "cpu": "95GIB"}

# Step 2: Create a data loading function (mirroring the example)
# --------------------------------------------------------------
def get_calibration_data():
    """
    This function loads, processes, and returns the calibration data as a list of strings,
    which is the format the library's internal loader expects.
    """
    print("Loading and preparing calibration data...")
    dataset_name = "Darkhn/WOF_V4_Combined_Dataset_deslopped_cleaned"
    try:
        calib_dataset = load_dataset(dataset_name, split="train")
    except Exception as e:
        print(f"FATAL: Could not load dataset '{dataset_name}'. Error: {e}")
        exit()

    # We need a temporary tokenizer to apply the chat template
    temp_tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    def remap_conversation(conversation_list):
        new_conversation = []
        for turn in conversation_list:
            role_from = turn.get("from"); content = turn.get("value")
            if not all([role_from, content, content.strip()]): continue
            if role_from == "system": role_to = "system"
            elif role_from == "human": role_to = "user"
            elif role_from == "gpt": role_to = "assistant"
            else: continue
            new_conversation.append({"role": role_to, "content": content})
        return new_conversation

    # Process the dataset to get a list of text strings
    texts = []
    for entry in calib_dataset:
        if "conversations" in entry and entry["conversations"]:
            remapped = remap_conversation(entry["conversations"])
            if remapped:
                formatted_text = temp_tokenizer.apply_chat_template(
                    remapped, tokenize=False, add_generation_prompt=False
                )
                if formatted_text and formatted_text.strip():
                    texts.append(formatted_text)
    
    print(f"Found {len(texts)} valid text samples in the dataset.")
    return texts

# Step 3: Load Model and Tokenizer
# --------------------------------
torch.cuda.empty_cache()
print("Loading model for quantization...")
# We MUST use max_memory and device_map to load a 70B model
model = AutoAWQForCausalLM.from_pretrained(
    model_path,
    safetensors=True,
    use_cache=False,
    max_memory=max_memory,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
print("Model loaded successfully.")

# Step 4: Quantize the Model (using the correct parameters from the example)
# -------------------------------------------------------------------------
print("Starting quantization process with correct parameters...")

# Load calibration data using our function
calibration_data = get_calibration_data()

# Check if we have data before proceeding
if not calibration_data:
    print("FATAL: No calibration data could be loaded. Aborting.")
    exit()

model.quantize(
    tokenizer,
    quant_config=quant_config,
    calib_data=calibration_data,          # Pass the list of strings
    max_calib_samples=128,                # Use the library's sample limiter
    max_calib_seq_len=1024,               # ** THE CRITICAL FIX: The correct parameter name **
    n_parallel_calib_samples=1            # Optional: Controls batching to prevent OOM
)
print("Quantization complete.")

# Step 5: Save the Quantized Model
# --------------------------------
print(f"Saving quantized model to: {quant_path}")
os.makedirs(quant_path, exist_ok=True)
model.save_quantized(quant_path)
tokenizer.save_pretrained(quant_path)
print(f'Model is quantized and saved at "{quant_path}"')