"""Tests for eval_harness.build_official_overrides.

Mirrors SAIR's evaluation_models.json payload construction exactly so
`--official-mode` produces the same OpenRouter requests as the official
Stage 1 judge repo (SAIRcompetition/equational-theories-stage1-judge).

Reference sources:
- https://github.com/SAIRcompetition/equational-theories-stage1-judge/blob/main/evaluation_models.json
- llm.py _build_body(): provider = {order, quantizations, allow_fallbacks}
- llm.py reasoning: {"effort": "low"} or {"effort": "none"}
- models.py _PROVIDER_NAMES: deepinfra → DeepInfra, novita → Novita
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eval_harness import build_official_overrides


# ---------------------------------------------------------------------------
# Full config fixtures mirroring the official evaluation_models.json
# ---------------------------------------------------------------------------

GPT_OSS_120B_CFG = {
    "official_params": {
        "provider": "deepinfra/bf16",
        "reasoning_effort": "low",
        "seed": 0,
        "max_tokens": 8192,
    }
}

LLAMA_CFG = {
    "official_params": {
        "provider": "deepinfra/fp8",
        "reasoning_effort": "none",
        "seed": 0,
        "max_tokens": 8192,
    }
}

GEMMA_CFG = {
    "official_params": {
        "provider": "novita/bf16",
        "reasoning_effort": "low",
        "seed": 0,
        "max_tokens": 8192,
    }
}

GEMMA_CFG_WITH_FALLBACKS = {
    "official_params": {
        "provider": "novita/bf16",
        "reasoning_effort": "low",
        "seed": 0,
        "max_tokens": 8192,
        "fallback_providers": ["Parasail", "Venice"],
    }
}


# ---------------------------------------------------------------------------
# gpt-oss-120b official payload
# ---------------------------------------------------------------------------

def test_gpt_oss_120b_max_tokens():
    out = build_official_overrides(GPT_OSS_120B_CFG)
    assert out["max_tokens"] == 8192


def test_gpt_oss_120b_seed():
    out = build_official_overrides(GPT_OSS_120B_CFG)
    assert out["seed"] == 0


def test_gpt_oss_120b_reasoning_low():
    out = build_official_overrides(GPT_OSS_120B_CFG)
    assert out["reasoning"] == {"effort": "low"}


def test_gpt_oss_120b_provider_order_deepinfra():
    out = build_official_overrides(GPT_OSS_120B_CFG)
    assert out["provider"]["order"] == ["DeepInfra"]


def test_gpt_oss_120b_provider_quantizations_bf16():
    out = build_official_overrides(GPT_OSS_120B_CFG)
    assert out["provider"]["quantizations"] == ["bf16"]


def test_gpt_oss_120b_provider_allow_fallbacks_false():
    out = build_official_overrides(GPT_OSS_120B_CFG)
    assert out["provider"]["allow_fallbacks"] is False


# ---------------------------------------------------------------------------
# llama-3.3-70b-instruct official payload (reasoning disabled, fp8)
# ---------------------------------------------------------------------------

def test_llama_reasoning_none():
    out = build_official_overrides(LLAMA_CFG)
    assert out["reasoning"] == {"effort": "none"}


def test_llama_provider_fp8():
    out = build_official_overrides(LLAMA_CFG)
    assert out["provider"]["order"] == ["DeepInfra"]
    assert out["provider"]["quantizations"] == ["fp8"]


def test_llama_seed_and_max_tokens():
    out = build_official_overrides(LLAMA_CFG)
    assert out["seed"] == 0
    assert out["max_tokens"] == 8192


# ---------------------------------------------------------------------------
# gemma-4-31b-it official payload (novita provider)
# ---------------------------------------------------------------------------

def test_gemma_provider_novita():
    out = build_official_overrides(GEMMA_CFG)
    assert out["provider"]["order"] == ["Novita"]
    assert out["provider"]["quantizations"] == ["bf16"]


def test_gemma_reasoning_low():
    out = build_official_overrides(GEMMA_CFG)
    assert out["reasoning"] == {"effort": "low"}


# ---------------------------------------------------------------------------
# Error handling: model without official_params
# ---------------------------------------------------------------------------

def test_missing_official_params_raises():
    cfg = {"openrouter": {"model_id": "deepseek/deepseek-v3.2"}}
    try:
        build_official_overrides(cfg)
    except ValueError as e:
        assert "official_params" in str(e)
        return
    raise AssertionError("expected ValueError for missing official_params")


# ---------------------------------------------------------------------------
# allow_fallbacks override (off by default, flipped by CLI flag)
# ---------------------------------------------------------------------------

def test_allow_fallbacks_default_false():
    # Existing behavior: without the flag, allow_fallbacks stays pinned off.
    out = build_official_overrides(GPT_OSS_120B_CFG)
    assert out["provider"]["allow_fallbacks"] is False


def test_allow_fallbacks_true_when_flag_set_gpt():
    out = build_official_overrides(GPT_OSS_120B_CFG, allow_fallbacks=True)
    assert out["provider"]["allow_fallbacks"] is True
    # Everything else still identical to default
    assert out["provider"]["order"] == ["DeepInfra"]
    assert out["provider"]["quantizations"] == ["bf16"]
    assert out["reasoning"] == {"effort": "low"}
    assert out["seed"] == 0
    assert out["max_tokens"] == 8192


def test_allow_fallbacks_true_when_flag_set_gemma():
    # The use case that drove this flag: let OpenRouter route past Novita
    # when Novita is capacity-exhausted.
    out = build_official_overrides(GEMMA_CFG, allow_fallbacks=True)
    assert out["provider"]["allow_fallbacks"] is True
    assert out["provider"]["order"] == ["Novita"]
    assert out["provider"]["quantizations"] == ["bf16"]


def test_allow_fallbacks_true_still_includes_reasoning_and_seed():
    # Make sure the flag doesn't accidentally strip other official-mode fields.
    out = build_official_overrides(LLAMA_CFG, allow_fallbacks=True)
    assert out["reasoning"] == {"effort": "none"}
    assert out["seed"] == 0
    assert out["max_tokens"] == 8192


def test_allow_fallbacks_explicit_false_matches_default():
    out_default = build_official_overrides(GPT_OSS_120B_CFG)
    out_explicit = build_official_overrides(GPT_OSS_120B_CFG, allow_fallbacks=False)
    assert out_default == out_explicit


# ---------------------------------------------------------------------------
# fallback_providers list: extends provider.order when allow_fallbacks=True
# ---------------------------------------------------------------------------

def test_fallback_providers_ignored_when_flag_off():
    # Without --official-fallbacks, the fallback list is ignored entirely
    # (strict pinning to the primary provider — matches SAIR's config).
    out = build_official_overrides(GEMMA_CFG_WITH_FALLBACKS, allow_fallbacks=False)
    assert out["provider"]["order"] == ["Novita"]
    assert out["provider"]["allow_fallbacks"] is False


def test_fallback_providers_appended_when_flag_on():
    # With --official-fallbacks, Novita stays first but Parasail+Venice are
    # appended as fallbacks.
    out = build_official_overrides(GEMMA_CFG_WITH_FALLBACKS, allow_fallbacks=True)
    assert out["provider"]["order"] == ["Novita", "Parasail", "Venice"]
    assert out["provider"]["allow_fallbacks"] is True
    # Quantization filter still applies to the whole list.
    assert out["provider"]["quantizations"] == ["bf16"]


def test_fallback_providers_missing_field_is_empty():
    # When no fallback_providers list is present in the config, fallbacks=True
    # still flips allow_fallbacks but doesn't extend the order.
    out = build_official_overrides(GEMMA_CFG, allow_fallbacks=True)
    assert out["provider"]["order"] == ["Novita"]
    assert out["provider"]["allow_fallbacks"] is True


# ---------------------------------------------------------------------------
# Provider tag edge cases
# ---------------------------------------------------------------------------

def test_provider_without_quantization():
    # "deepinfra" with no slash → order set, no quantizations key
    cfg = {
        "official_params": {
            "provider": "deepinfra",
            "reasoning_effort": "low",
            "seed": 0,
            "max_tokens": 8192,
        }
    }
    out = build_official_overrides(cfg)
    assert out["provider"]["order"] == ["DeepInfra"]
    assert "quantizations" not in out["provider"]
    assert out["provider"]["allow_fallbacks"] is False


def test_provider_display_name_passthrough():
    # Already-capitalized display name passes through unchanged.
    cfg = {
        "official_params": {
            "provider": "DeepInfra/bf16",
            "reasoning_effort": "low",
            "seed": 0,
            "max_tokens": 8192,
        }
    }
    out = build_official_overrides(cfg)
    assert out["provider"]["order"] == ["DeepInfra"]


def test_no_reasoning_key_when_reasoning_effort_missing():
    # If reasoning_effort is omitted from official_params, no reasoning key emitted.
    cfg = {
        "official_params": {
            "provider": "deepinfra/bf16",
            "seed": 0,
            "max_tokens": 8192,
        }
    }
    out = build_official_overrides(cfg)
    assert "reasoning" not in out


def test_temperature_not_in_output():
    # Temperature must never come from official_params — the harness must
    # leave temperature decisions to the existing params resolution.
    out = build_official_overrides(GPT_OSS_120B_CFG)
    assert "temperature" not in out


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _run_all():
    tests = [(n, obj) for n, obj in sorted(globals().items())
             if n.startswith("test_") and callable(obj)]
    passed, failed = 0, []
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except AssertionError:
            failed.append((name, "AssertionError", traceback.format_exc(limit=2)))
        except Exception as e:
            failed.append((name, type(e).__name__, traceback.format_exc(limit=2)))
    total = len(tests)
    print(f"\n{passed}/{total} tests passed")
    if failed:
        print(f"\n{len(failed)} FAILURES:")
        for name, kind, tb in failed:
            print(f"\n--- {name} [{kind}] ---")
            print(tb)
        sys.exit(1)
    print("All green.")


if __name__ == "__main__":
    _run_all()
