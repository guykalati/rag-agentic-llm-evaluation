"""Small checks for the fixed byte-level training contract."""

import math

import torch

from prepare import CONTEXT, validation_bpb
from train import Model


class Uniform(torch.nn.Module):
    def forward(self, x):
        return torch.zeros((*x.shape, 256), device=x.device)


device = torch.device("cpu")
data = torch.arange(256, dtype=torch.uint8).repeat(3)
assert math.isclose(validation_bpb(Uniform(), data, device)["val_bpb"], 8.0, abs_tol=1e-5)
if torch.cuda.is_available():
    gpu = torch.device("cuda")
    assert math.isclose(validation_bpb(Uniform().to(gpu), data.to(gpu), gpu)["val_bpb"],
                        8.0, abs_tol=1e-5)
torch.manual_seed(7)
model = Model().eval()
x = torch.randint(0, 256, (1, CONTEXT))
altered = x.clone()
altered[:, 100:] = torch.randint(0, 256, (1, CONTEXT - 100))
with torch.no_grad():
    left = model(x)[:, :100]
    right = model(altered)[:, :100]
torch.testing.assert_close(left, right, atol=1e-5, rtol=1e-5)
print("uniform CPU/GPU validation and causal-prefix checks passed")
