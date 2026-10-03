"""Editable single-file byte Transformer training candidate."""

import json
import os
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from prepare import CONTEXT, SEED, TRAIN_SECONDS, sha256, validation_bpb


SEED = 20260929


class Model(nn.Module):
    def __init__(self):
        super().__init__()
        width = 480
        self.token = nn.Embedding(256, width)
        self.position = nn.Embedding(CONTEXT, width)
        layer = nn.TransformerEncoderLayer(width, 6, 1536, dropout=0.0,
                                            batch_first=True, norm_first=True)
        self.blocks = nn.TransformerEncoder(layer, 4, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(width)
        self.head = nn.Linear(width, 256, bias=False)
        self.head.weight = self.token.weight
        self.register_buffer("mask", torch.triu(torch.ones(CONTEXT, CONTEXT, dtype=torch.bool), 1))

    def forward(self, x):
        length = x.shape[1]
        positions = torch.arange(length, device=x.device)
        h = self.token(x) + self.position(positions)
        return self.head(self.norm(self.blocks(h, mask=self.mask[:length, :length])))


def main():
    if not torch.cuda.is_available():
        raise RuntimeError("one CUDA GPU required")
    data_dir = Path(os.environ.get("EXPERIMENT_DATA_DIR", "data"))
    output = Path(os.environ.get("EXPERIMENT_OUTPUT_DIR", "output"))
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((data_dir / "data_manifest.json").read_text())
    for split in ("train", "val"):
        if sha256(data_dir / f"{split}.bin") != manifest[f"{split}_sha256"]:
            raise ValueError(f"fixed {split} data changed")
    if manifest["context"] != CONTEXT or manifest["training_seconds"] != TRAIN_SECONDS:
        raise ValueError("fixed training contract changed")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    device = torch.device("cuda")
    train = torch.from_numpy(np.fromfile(data_dir / "train.bin", dtype=np.uint8)).to(device)
    val = torch.from_numpy(np.fromfile(data_dir / "val.bin", dtype=np.uint8)).to(device)
    model = Model().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    offsets = torch.arange(CONTEXT + 1, device=device)
    torch.cuda.reset_peak_memory_stats()
    steps, last_loss = 0, None
    start = time.monotonic()
    while True:
        model.train()
        begin = torch.randint(0, len(train) - CONTEXT - 1, (32,), device=device)
        block = train[begin[:, None] + offsets].long()
        optimizer.zero_grad(set_to_none=True)
        logits = model(block[:, :-1])
        loss = F.cross_entropy(logits.reshape(-1, 256), block[:, 1:].reshape(-1))
        loss.backward()
        optimizer.step()
        steps += 1
        if steps % 50 == 0:
            torch.cuda.synchronize()
            last_loss = float(loss.item())
            print(json.dumps({"step": steps, "train_loss_nats": last_loss,
                              "training_seconds": round(time.monotonic() - start, 1)}), flush=True)
        if time.monotonic() - start >= TRAIN_SECONDS:
            break
    torch.cuda.synchronize()
    training_seconds = time.monotonic() - start
    checkpoint = output / "model.pt"
    torch.save({"state_dict": model.state_dict(), "steps": steps,
                "train_sha256": manifest["train_sha256"],
                "val_sha256": manifest["val_sha256"]}, checkpoint)
    score = validation_bpb(model, val, device)
    result = {"status": "success", "metric_name": "val_bpb", "metric_value": score["val_bpb"],
              **score, "training_seconds": training_seconds,
              "train_loss_nats_last_logged": last_loss, "steps": steps,
              "seed": SEED, "configuration": "larger",
              "parameter_count": sum(p.numel() for p in model.parameters()),
              "gpu_name": torch.cuda.get_device_name(),
              "gpu_peak_bytes": torch.cuda.max_memory_allocated(),
              "torch_version": torch.__version__,
              "prepare_sha256": sha256(Path(__file__).with_name("prepare.py")),
              "train_sha256": sha256(Path(__file__)),
              "data_manifest_sha256": sha256(data_dir / "data_manifest.json"),
              "checkpoint_sha256": sha256(checkpoint)}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
