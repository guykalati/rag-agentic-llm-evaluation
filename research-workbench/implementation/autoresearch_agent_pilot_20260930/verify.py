"""Independently recompute a saved candidate's frozen validation metric."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch

from prepare import sha256, validation_bpb
from train import Model


def main(data_dir, output_dir):
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA verifier required")
    manifest = json.loads((data_dir / "data_manifest.json").read_text())
    result = json.loads((output_dir / "result.json").read_text())
    if sha256(data_dir / "train.bin") != manifest["train_sha256"] or \
       sha256(data_dir / "val.bin") != manifest["val_sha256"] or \
       sha256(data_dir / "data_manifest.json") != result["data_manifest_sha256"] or \
       sha256(Path(__file__).with_name("train.py")) != result["train_sha256"]:
        raise ValueError("candidate or fixed data changed")
    checkpoint = output_dir / "model.pt"
    if sha256(checkpoint) != result["checkpoint_sha256"]:
        raise ValueError("checkpoint changed")
    saved = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if saved["train_sha256"] != manifest["train_sha256"] or \
       saved["val_sha256"] != manifest["val_sha256"]:
        raise ValueError("checkpoint provenance changed")
    device = torch.device("cuda")
    model = Model().to(device)
    model.load_state_dict(saved["state_dict"])
    val = torch.from_numpy(np.fromfile(data_dir / "val.bin", dtype=np.uint8)).to(device)
    score = validation_bpb(model, val, device)
    if not math.isclose(score["val_bpb"], result["val_bpb"], rel_tol=0, abs_tol=1e-5) or \
       score["validation_bytes_scored"] != result["validation_bytes_scored"]:
        raise ValueError("independent validation score disagrees")
    output = {"verified": True, "independent_val_bpb": score["val_bpb"],
              "validation_bytes_scored": score["validation_bytes_scored"],
              "checkpoint_sha256": result["checkpoint_sha256"]}
    (output_dir / "verified.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    main(args.data_dir, args.output_dir)
