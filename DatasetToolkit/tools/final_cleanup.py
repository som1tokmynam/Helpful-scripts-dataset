# tools/final_cleanup.py
import json
import logging
from pathlib import Path
from tqdm import tqdm

# Configure logging to integrate with the GUI's handler
logger = logging.getLogger(__name__)

def final_cleanup_main(
    input_file: str,
    output_file: str,
    conversation_key: str = 'conversations',
    role_key: str = 'from',
    value_key: str = 'value'
) -> None:
    """
    Performs a final, aggressive cleanup of a JSONL dataset.

    This function removes entire conversations (lines) if they meet any of the
    following criteria:
    1. Contain the substring "{narrator}" (case-insensitive) in any turn's value.
    2. Have consecutive turns from the same role (e.g., 'human' followed by 'human').

    Args:
        input_file (str): Path to the input JSONL file.
        output_file (str): Path to the output JSONL file.
        conversation_key (str): Key for the list of conversation turns.
        role_key (str): Key for the speaker's role in a turn.
        value_key (str): Key for the text content in a turn.
    """
    in_path = Path(input_file)
    out_path = Path(output_file)

    if not in_path.is_file():
        logger.error(f"Input file not found: {in_path}")
        raise FileNotFoundError(f"Input file not found: {in_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines_removed = 0
    total_lines = 0
    lines_kept = 0

    try:
        # First, count total lines for a nice progress bar
        with in_path.open('r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)

        if total_lines == 0:
            logger.warning("Input file is empty. Nothing to do.")
            out_path.touch() # Create an empty output file
            return

        with in_path.open('r', encoding='utf-8') as infile, \
             out_path.open('w', encoding='utf-8') as outfile:

            for line in tqdm(infile, total=total_lines, desc="Performing final cleanup"):
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed JSON line: {line.strip()}")
                    continue

                if conversation_key not in data or not isinstance(data.get(conversation_key), list):
                    logger.warning(f"Skipping line with missing/invalid conversation key: {line.strip()}")
                    continue

                conversations = data[conversation_key]
                should_remove = False
                last_role = None

                for turn in conversations:
                    if not isinstance(turn, dict):
                        continue  # Skip malformed turns

                    # Condition 1: Check for {narrator}
                    content = turn.get(value_key, "")
                    if isinstance(content, str) and "{narrator}" in content.lower():
                        should_remove = True
                        break

                    # Condition 2: Check for consecutive turns
                    current_role = turn.get(role_key)
                    if current_role is not None and current_role == last_role:
                        should_remove = True
                        break
                    last_role = current_role

                if should_remove:
                    lines_removed += 1
                else:
                    outfile.write(line)
                    lines_kept += 1

        logger.info("Final cleanup complete.")
        logger.info(f"Total lines processed: {total_lines}")
        logger.info(f"Lines removed due to criteria: {lines_removed}")
        logger.info(f"Lines kept: {lines_kept}")
        logger.info(f"Cleaned file saved to: {out_path}")

    except Exception as e:
        logger.critical(f"An unexpected error occurred during final cleanup: {e}", exc_info=True)
        raise