import torch
import os
import argparse

def main():
    """
    Inspects and optionally modifies the learning rate in a Hugging Face Trainer's
    optimizer.pt file within a specified checkpoint.
    """
    parser = argparse.ArgumentParser(
        description="Inspect or modify the learning rate in a PyTorch optimizer checkpoint."
    )
    parser.add_argument(
        "checkpoint_path",
        type=str,
        help="Path to the checkpoint directory (e.g., ./outputs/qlora-out/checkpoint-500)."
    )
    parser.add_argument(
        "--new_lr",
        type=float,
        default=None, # By default, we are in 'inspect' mode
        help="The new learning rate to set. If not provided, the script will only display the current LR."
    )
    args = parser.parse_args()

    # Construct the full path to the optimizer file
    optimizer_path = os.path.join(args.checkpoint_path, "optimizer.pt")

    # --- Safety Check ---
    if not os.path.exists(optimizer_path):
        print(f"❌ Error: Optimizer file not found at '{optimizer_path}'")
        print("Please ensure the checkpoint path is correct and it contains an 'optimizer.pt' file.")
        return

    # --- Load the Optimizer State ---
    print(f"🔎 Loading optimizer state from '{optimizer_path}'...")
    # We load to CPU to avoid needing a GPU for this simple script
    try:
        optimizer_state_dict = torch.load(optimizer_path, map_location="cpu")
    except Exception as e:
        print(f"❌ Error: Failed to load the optimizer file. It might be corrupted. Error: {e}")
        return
        
    # --- Inspect and/or Modify ---
    if "param_groups" not in optimizer_state_dict:
        print("❌ Error: Could not find 'param_groups' in the optimizer state dictionary.")
        print("This file does not appear to be a standard PyTorch optimizer state.")
        return

    param_groups = optimizer_state_dict['param_groups']
    print(f"✅ Found {len(param_groups)} parameter group(s) in the optimizer state.")

    # --- The Core Logic ---
    is_modify_mode = args.new_lr is not None

    if is_modify_mode:
        print("\n🔧 MODIFY MODE: Updating learning rate...")
    else:
        print("\n🔍 INSPECT MODE: Displaying current learning rate(s)...")

    for i, param_group in enumerate(param_groups):
        old_lr = param_group.get('lr', 'Not Found')
        print(f"  - Group {i}: Current learning rate is {old_lr}")

        if is_modify_mode:
            param_group['lr'] = args.new_lr
            print(f"    -> New learning rate set to {param_group['lr']}")

    # --- Save the Modified State Back (only in modify mode) ---
    if is_modify_mode:
        print(f"\n💾 Saving modified optimizer state back to '{optimizer_path}'...")
        try:
            torch.save(optimizer_state_dict, optimizer_path)
            print("✅ Success! The learning rate has been updated in the checkpoint.")
        except Exception as e:
            print(f"❌ Error: Failed to save the updated optimizer file. Error: {e}")
    else:
        print("\n✅ Done. No changes were made.")


if __name__ == "__main__":
    main()