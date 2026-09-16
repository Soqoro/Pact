from __future__ import annotations

import importlib.metadata
import importlib.util
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .util import digest, file_hash


def versions() -> dict:
    return dict(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions() if d.metadata["Name"]))


def runtime_fingerprint() -> str:
    packages = {}
    for name in ("torch", "transformers", "peft", "accelerate", "tokenizers", "huggingface-hub", "jinja2", "numpy", "safetensors"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    result = {"python": platform.python_version(), "platform": platform.system(),
              "machine": platform.machine(), "packages": packages}
    if importlib.util.find_spec("torch"):
        import torch
        result.update(cuda=torch.version.cuda, gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
    return digest(result)


def code_identity(root: Path) -> dict:
    def git(*args):
        p = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True)
        return p.stdout.strip() if p.returncode == 0 else None
    files = [p for folder in ("src", "configs", "experiments") for p in (root / folder).rglob("*")
             if p.is_file() and "__pycache__" not in p.parts and not any(x.endswith(".egg-info") for x in p.parts)]
    files += [root / "pyproject.toml"] if (root / "pyproject.toml").is_file() else []
    return {"git_commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain")),
            "source_hash": digest({p.relative_to(root).as_posix(): file_hash(p) for p in sorted(files)})}


def doctor(scratch: Path, persistent: Path | None = None, config=None) -> dict:
    scratch.mkdir(parents=True, exist_ok=True)
    result = {"python": sys.version, "platform": platform.platform(), "packages": versions(),
              "disk_free_bytes": shutil.disk_usage(scratch).free, "persistent_writable": None,
              "gpu_count": 0, "gpu": None, "torch": None, "cuda": None,
              "attention_kernels": None, "ram_bytes": None, "warnings": [], "errors": []}
    if importlib.util.find_spec("psutil"):
        import psutil
        result["ram_bytes"] = psutil.virtual_memory().total
    if persistent:
        persistent.mkdir(parents=True, exist_ok=True)
        import tempfile
        with tempfile.TemporaryFile(dir=persistent) as stream:
            stream.write(b"PACT storage preflight")
            stream.flush()
        result["persistent_writable"] = True
    if importlib.util.find_spec("torch"):
        import torch
        result.update(torch=torch.__version__, cuda=torch.version.cuda, gpu_count=torch.cuda.device_count(),
                      attention_kernels={"sdpa": hasattr(torch.nn.functional, "scaled_dot_product_attention")})
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            result["gpu"] = {"name": p.name, "memory_bytes": p.total_memory,
                             "capability": list(torch.cuda.get_device_capability(0)), "bf16": torch.cuda.is_bf16_supported()}
    if config and config.backend == "transformers":
        for package in ("transformers", "peft", "accelerate", "pyarrow", "torch"):
            if not importlib.util.find_spec(package):
                result["errors"].append(f"Missing package: {package}")
        if config.model.device == "cuda" and result["gpu_count"] != 1:
            result["errors"].append("Exactly one visible CUDA GPU required")
        if config.model.precision == "bfloat16" and config.model.device == "cuda" and not (result["gpu"] or {}).get("bf16"):
            result["errors"].append("Requested BF16 unsupported")
        for package, expected in (("transformers", "4.57.6"), ("peft", "0.18.1"), ("accelerate", "1.12.0"), ("pyarrow", "22.0.0")):
            try:
                actual = importlib.metadata.version(package)
                if actual != expected:
                    result["errors"].append(f"{package} must be {expected}; found {actual}")
            except importlib.metadata.PackageNotFoundError:
                pass
        result["model_access"] = {"status": "not_checked", "reason": "preflight errors"}
        if not result["errors"]:
            try:
                from huggingface_hub import HfApi
                info = HfApi().model_info(config.model.name, revision=config.model.revision)
                if info.sha != config.model.revision:
                    raise ValueError("Resolved model revision differs from configured SHA")
                result["model_access"] = {"status": "verified_metadata", "revision": info.sha}
                if config.model.device == "cuda":
                    import torch
                    sample = torch.ones((1, 1, 8, 16), device="cuda", dtype=getattr(torch, config.model.precision))
                    torch.nn.functional.scaled_dot_product_attention(sample, sample, sample).sum().item()
                    result["attention_kernels"].update(sdpa_executed=True,
                        supported_architectures=torch.cuda.get_arch_list(), flash_enabled=torch.backends.cuda.flash_sdp_enabled(),
                        math_enabled=torch.backends.cuda.math_sdp_enabled())
                    del sample
            except Exception as exc:
                from .util import redact
                result["errors"].append("Model access/kernel preflight: " + redact(str(exc)))
    result["runtime_fingerprint"] = runtime_fingerprint()
    return result
