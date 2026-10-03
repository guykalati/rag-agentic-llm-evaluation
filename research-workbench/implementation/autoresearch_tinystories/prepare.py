"""Fixed TinyStories byte-data preparation and validation for experiment mode."""

import argparse
import hashlib
import json
import math
from pathlib import Path


SOURCE = "karpathy/tinystories-gpt4-clean"
REVISION = "0397e27157956705a0260709da3095bb9c43d6a7"
TRAIN_TARGET = 128 * 1024 * 1024
VAL_TARGET = 2 * 1024 * 1024
MAX_ROWS = 300_000
CONTEXT = 256
TRAIN_SECONDS = 300
SEED = 20260929


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(data_dir):
    from datasets import load_dataset

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest = data_dir / "data_manifest.json"
    if manifest.exists():
        saved = json.loads(manifest.read_text())
        for split in ("train", "val"):
            if sha256(data_dir / f"{split}.bin") != saved[f"{split}_sha256"]:
                raise ValueError(f"saved {split} bytes changed")
        return saved
    train_path, val_path = data_dir / "train.bin", data_dir / "val.bin"
    if train_path.exists() or val_path.exists():
        raise FileExistsError("partial data found; inspect before resuming")
    source = load_dataset(SOURCE, split="train", streaming=True, revision=REVISION)
    seen, counts = set(), {"train": 0, "val": 0}
    duplicates, scanned = 0, 0
    with train_path.open("wb") as train, val_path.open("wb") as val:
        for row in source:
            scanned += 1
            story = row["text"].encode("utf-8")
            digest = hashlib.sha256(story).digest()
            if digest in seen:
                duplicates += 1
                continue
            seen.add(digest)
            split = "val" if int.from_bytes(digest[:4], "big") % 16 == 0 else "train"
            target = VAL_TARGET if split == "val" else TRAIN_TARGET
            if counts[split] < target:
                (val if split == "val" else train).write(story + b"\n\n")
                counts[split] += len(story) + 2
            if counts["train"] >= TRAIN_TARGET and counts["val"] >= VAL_TARGET:
                break
            if scanned >= MAX_ROWS:
                raise RuntimeError("source row cap reached before data quotas")
    output = {"source": SOURCE, "revision": REVISION, "license": "cdla-sharing-1.0",
              "tokenizer": "UTF-8 bytes; vocabulary 256", "split_rule": "SHA256(text) first 32 bits mod 16 == 0 gives validation",
              "exact_text_duplicates_skipped": duplicates, "source_rows_scanned": scanned,
              "train_bytes": counts["train"], "val_bytes": counts["val"],
              "train_sha256": sha256(train_path), "val_sha256": sha256(val_path),
              "context": CONTEXT, "training_seconds": TRAIN_SECONDS,
              "validation_rule": "all nonoverlapping 256-byte windows with one-byte targets"}
    manifest.write_text(json.dumps(output, indent=2) + "\n")
    return output


def validation_bpb(model, val_bytes, device, batch_size=64):
    import torch
    from torch.nn import functional as F

    expected_device = (torch.device("cuda", torch.cuda.current_device())
                       if device.type == "cuda" and device.index is None else device)
    if val_bytes.dtype != torch.uint8 or val_bytes.device != expected_device:
        raise ValueError("expected fixed validation bytes on model device")
    n_sequences = (len(val_bytes) - 1) // CONTEXT
    if n_sequences < 1:
        raise ValueError("validation data too short")
    offsets = torch.arange(CONTEXT + 1, device=device)
    loss_sum, tokens = 0.0, 0
    model.eval()
    with torch.no_grad():
        for start in range(0, n_sequences, batch_size):
            stops = torch.arange(start, min(start + batch_size, n_sequences), device=device)
            block = val_bytes[stops[:, None] * CONTEXT + offsets].long()
            logits = model(block[:, :-1])
            target = block[:, 1:]
            loss_sum += F.cross_entropy(logits.reshape(-1, 256), target.reshape(-1),
                                        reduction="sum").item()
            tokens += target.numel()
    return {"val_bpb": loss_sum / tokens / math.log(2), "validation_bytes_scored": tokens}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    print(json.dumps(prepare(parser.parse_args().data_dir), indent=2))
