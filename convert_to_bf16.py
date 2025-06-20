import torch
from safetensors.torch import load_file, save_file
import sys
import os

def convert_to_bf16(fp32_file_path, bf16_file_path):
    """
    Loads an fp32 .safetensor file, converts all floating-point
    tensors to bfloat16, and saves them to a new .safetensor file.
    """
    try:
        print(f"Loading fp32 weights from: {fp32_file_path}")
        # Load the fp32 state dictionary from the .safetensor file
        state_dict_fp32 = load_file(fp32_file_path)

        state_dict_bf16 = {}
        print("Converting tensors to bfloat16...")

        # Iterate through all tensors in the state dictionary
        for key, tensor in state_dict_fp32.items():
            # Check if the tensor is a floating-point type before converting
            if torch.is_floating_point(tensor):
                state_dict_bf16[key] = tensor.to(torch.bfloat16)
            else:
                # Keep non-floating point tensors (like integers) in their original format
                state_dict_bf16[key] = tensor

        print(f"Saving bf16 weights to: {bf16_file_path}")
        # Save the new bfloat16 state dictionary
        save_file(state_dict_bf16, bf16_file_path)

        print("Conversion successful!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_to_bf16.py <path_to_fp32_safetensor_file> <path_to_output_bf16_safetensor_file>")
        sys.exit(1)

    fp32_path = sys.argv[1]
    bf16_path = sys.argv[2]

    if not os.path.exists(fp32_path):
        print(f"Error: Input file not found at {fp32_path}")
        sys.exit(1)

    convert_to_bf16(fp32_path, bf16_path)