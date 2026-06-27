from __future__ import annotations

from services.compliance.k_anonymity import passes_k_anonymity, public_bucket_label


def test_low_sample_bucket_hidden():
    assert not passes_k_anonymity(19, k=20)
    assert public_bucket_label(19, k=20) == "样本不足"
    assert passes_k_anonymity(20, k=20)

