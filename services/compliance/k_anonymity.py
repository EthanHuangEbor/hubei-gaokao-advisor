from __future__ import annotations


def passes_k_anonymity(sample_count: int, k: int = 20) -> bool:
    return sample_count >= k


def public_bucket_label(sample_count: int, k: int = 20) -> str:
    if passes_k_anonymity(sample_count, k):
        return "同位次区间历史可达专业组参考"
    return "样本不足"

