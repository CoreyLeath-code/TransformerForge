"""
attention.py
───────────────────────────────────────────────────────────────────────────
Python wrapper for C++17 `libfastattn.so` (CPU flash-attention).

• fast_attention_np(...)  → NumPy input / output
• fast_attention_torch(...) → PyTorch tensors (CPU fallback to torch SDPA)

If `libfastattn.so` is missing the call gracefully falls back to
torch.nn.functional.scaled_dot_product_attention (PyTorch ≥ 2.0).
"""

from __future__ import annotations
import ctypes
from pathlib import Path

import numpy as np
import torch
from torch import Tensor

# ------------------------------------------------------------------ #
# 1. Attempt to load shared library
# ------------------------------------------------------------------ #
LIB_PATH = Path(__file__).resolve().parent.parent / "cpp" / "libfastattn.so"
_fastattn = None
if LIB_PATH.is_file():
    _fastattn = ctypes.cdll.LoadLibrary(str(LIB_PATH))
    _fastattn.fast_attention.restype = None  # void
    _fastattn.fast_attention.argtypes = (
        ctypes.POINTER(ctypes.c_float),  # q
        ctypes.POINTER(ctypes.c_float),  # k
        ctypes.POINTER(ctypes.c_float),  # v
        ctypes.POINTER(ctypes.c_float),  # out
        ctypes.c_size_t,                 # seq_len
        ctypes.c_size_t,                 # d_k
        ctypes.c_size_t,                 # d_v
        ctypes.c_float,                  # scale
    )
else:
    print("⚠️  libfastattn.so not found; defaulting to torch SDPA.")


# ------------------------------------------------------------------ #
# 2. NumPy wrapper
# ------------------------------------------------------------------ #
def fast_attention_np(
    q: np.ndarray, k: np.ndarray, v: np.ndarray
) -> np.ndarray:
    """
    Compute scaled dot-product attention (single head, batch=1).

    Shapes
    ------
    q, k : (seq_len, d_k)
    v    : (seq_len, d_v)
    Returns
    -------
    out  : (seq_len, d_v)
    """
    assert q.ndim == k.ndim == v.ndim == 2
    seq_len, d_k = q.shape
    _seq_len, d_v = v.shape
    assert _seq_len == seq_len and k.shape == q.shape

    out = np.empty((seq_len, d_v), dtype=np.float32)
    scale = 1.0 / np.sqrt(d_k)

    if _fastattn:
        _fastattn.fast_attention(
            q.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            k.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            v.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ctypes.c_size_t(seq_len),
            ctypes.c_size_t(d_k),
            ctypes.c_size_t(d_v),
            ctypes.c_float(scale),
        )
    else:
        # torch fallback
        out[:] = fast_attention_torch(
            torch.from_numpy(q), torch.from_numpy(k), torch.from_numpy(v)
        ).numpy()
    return out


# ------------------------------------------------------------------ #
# 3. PyTorch wrapper / fallback
# ------------------------------------------------------------------ #
def fast_attention_torch(q: Tensor, k: Tensor, v: Tensor) -> Tensor:
    """
    PyTorch single-head SDPA (fallback). Expects shape (seq, d).
    """
    seq_len, d_k = q.shape
    scale = 1.0 / np.sqrt(d_k)
    q = q.unsqueeze(0)  # (1, seq, d)
    k = k.unsqueeze(0)
    v = v.unsqueeze(0)
    attn = torch.softmax((q @ k.transpose(-2, -1)) * scale, dim=-1)
    return (attn @ v).squeeze(0)  # (seq, d_v)


# ------------------------------------------------------------------ #
# 4. Simple CLI demo
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    np.random.seed(0)
    q = np.random.rand(4, 8).astype(np.float32)
    k = np.random.rand(4, 8).astype(np.float32)
    v = np.random.rand(4, 16).astype(np.float32)

    out = fast_attention_np(q, k, v)
    print("Output shape:", out.shape)
    print("First row (trunc):", out[0, :5])
