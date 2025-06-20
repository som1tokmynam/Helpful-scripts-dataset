#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["logbar", "safetensors", "torch", "peft"]
# ///

# Usage: python merge_lora.py input_path lora_path output_path
# Output path is created if it doesn't exist

import argparse
import os
import re
import shutil
import math
from pathlib import Path

import safetensors
import torch
from logbar import LogBar

import peft

log = LogBar.shared()

parser = argparse.ArgumentParser()
parser.add_argument('input_path', type=str, help='The path to the input directory.')
parser.add_argument('lora_path', type=str, help='The path to the LoRA directory.')
parser.add_argument('output_path', type=str, help='The path to the output directory.')
parser.add_argument('--no-gpu', action='store_true', help='Use CPU for merging.')
args = parser.parse_args()

input_path, lora_path, output_path = Path(args.input_path), Path(args.lora_path), Path(args.output_path)
os.makedirs(output_path, exist_ok=True)

lora_config = peft.LoraConfig.from_json_file(lora_path / 'adapter_config.json')
try:
    if lora_config["use_rslora"] or 1/0: # throw error if not rslora to avoid duplicate code
        scale = lora_config['lora_alpha'] / math.sqrt(lora_config['r'])
except:
    scale = lora_config['lora_alpha'] / lora_config['r']

log.debug(f"Lora scaling factor: x{scale}")

device = 'cpu' if args.no_gpu else 'cuda'

log.info('Loading LoRA model...')

# Check if we have adapter_model.bin or adapter_model.safetensors
if (lora_path / 'adapter_model.safetensors').exists():
    lora_state = safetensors.torch.load_file(lora_path / 'adapter_model.safetensors')
    if not args.no_gpu:
        # Move mapped entries to cuda
        for key, value in log.pb(lora_state.items()):
            lora_state[key] = value.to('cuda')
else:
    lora_state = torch.load(lora_path / 'adapter_model.bin', map_location=device)


def find_lora_weights(key):
    lora_A = None
    lora_B = None
    for lora_key, lora_weight in lora_state.items():
        if key.strip('.weight') in lora_key:
            if 'lora_A' in lora_key:
                lora_A = lora_weight
            elif 'lora_B' in lora_key:
                lora_B = lora_weight
            else:
                raise RuntimeError()
    assert not ((lora_A is None) ^ (lora_B is None))
    return lora_A, lora_B


shards = []
for shard in input_path.glob('model*.safetensors'):
    shards.append(shard)

log.info('Copying unmergable files to output')
for filepath in input_path.glob('*'):
    if filepath in shards:
        continue
    filepath = Path(filepath)
    if filepath.is_dir():
        continue
    if filepath.suffix == '.gguf':
        # Skip unrelated stray quantizations
        continue
    if filepath.suffix == '.safetensors':
        # Consolidated, possibly
        continue
    log.debug(f'copying {filepath.name} to output')
    shutil.copy(filepath, output_path)

pbar = log.pb(shards).title('Merging and copying state_dict to output').manual()
found = 0
for shard in pbar:
    tensors = {}
    with safetensors.safe_open(shard, framework='pt', device=device) as f:
        metadata = f.metadata()
        for key in f.keys():
            lora_key = re.sub(r'^language_model\.', '', key)
            tensor = f.get_tensor(key)
            lora_A, lora_B = find_lora_weights(lora_key)
            if lora_A is not None:
                found += 1
                pbar.subtitle(f'found lora weights for {key}: {lora_A.size()}, {lora_B.size()}')
                old_type = tensor.dtype
                tensor = tensor.to(torch.float32)
                tensor += scale * lora_B.to(torch.float32) @ lora_A.to(torch.float32)
                tensor = tensor.to(old_type)
            tensors[key] = tensor
            pbar.draw()
        safetensors.torch.save_file(tensors, output_path / shard.name, metadata=metadata)
log.info(f"Applied LoRA to {found} tensors.")
log.info(f"Moving tokenizer from {lora_path} to {output_path}")
shutil.copy(lora_path / 'tokenizer.json', output_path)
shutil.copy(lora_path / 'tokenizer_config.json', output_path)
shutil.copy(lora_path / 'special_tokens_map.json', output_path)
