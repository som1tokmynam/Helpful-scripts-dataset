import torch
import os
import argparse

def main():
    """
    Inspects and optionally modifies the base learning rate(s) in a Hugging Face
    Trainer's scheduler.pt file within a specified checkpoint.
    """
    parser = argparse.ArgumentParser(
        description="Inspect or modify the base learning rate in a PyTorch scheduler checkpoint."
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
        help="The new base learning rate to set. If not provided, will only display the current base_lrs."
    )
    args = parser.parse_args()

    # Construct the full path to the scheduler file
    scheduler_path = os.path.join(args.checkpoint_path, "scheduler.pt")

    # --- Safety Check ---
    if not os.path.exists(scheduler_path):
        print(f"❌ Error: Scheduler file not found at '{scheduler_path}'")
        return

    # --- Load the Scheduler State ---
    print(f"🔎 Loading scheduler state from '{scheduler_path}'...")
    try:
        scheduler_state_dict = torch.load(scheduler_path, map_location="cpu")
    except Exception as e:
        print(f"❌ Error: Failed to load the scheduler file. It might be corrupted. Error: {e}")
        return
        
    # --- The Core Logic for Schedulers ---
    key_to_find = 'base_lrs'
    if key_to_find not in scheduler_state_dict:
        print(f"❌ Error: Could not find the key '{key_to_find}' in the scheduler state.")
        print("This may not be a standard Hugging Face scheduler state dictionary.")
        return

    is_modify_mode = args.new_lr is not None

    if is_modify_mode:
        print("\n🔧 MODIFY MODE: Updating base learning rate(s)...")
    else:
        print("\n🔍 INSPECT MODE: Displaying current base learning rate(s)...")

    old_lrs = scheduler_state_dict[key_to_find]
    print(f"  - Found old base_lrs: {old_lrs}")

    if is_modify_mode:
        # Create a new list with the new LR, matching the length of the old one
        new_lrs = [args.new_lr for _ in old_lrs]
        scheduler_state_dict[key_to_find] = new_lrs
        print(f"    -> New base_lrs set to: {new_lrs}")

    # --- Save the Modified State Back (only in modify mode) ---
    if is_modify_mode:
        print(f"\n💾 Saving modified scheduler state back to '{scheduler_path}'...")
        try:
            torch.save(scheduler_state_dict, scheduler_path)
            print("✅ Success! The scheduler's base learning rate has been updated.")
        except Exception as e:
            print(f"❌ Error: Failed to save the updated scheduler file. Error: {e}")
    else:
        print("\n✅ Done. No changes were made.")

if __name__ == "__main__":
    main()