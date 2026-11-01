"""Grok-only model routing via direct xAI API (OpenAI-compatible)."""
from __future__ import annotations

import os
import random
from pathlib import Path

import openai
import yaml

from app.spend import SpendLimitError, check_can_spend, estimate_cost, log_call

ROUTING_PATH = Path(__file__).resolve().parent.parent / "model_routing.yaml"
XAI_BASE_URL = "https://api.x.ai/v1"

with open(ROUTING_PATH) as f:
    _ROUTING = yaml.safe_load(f)

MODELS = _ROUTING["models"]
DEFAULTS = _ROUTING["defaults"]


def list_models() -> list[str]:
    return list(MODELS.keys())


def _resolve_params(config: dict) -> dict:
    resolved = {}
    for k, v in config.items():
        if isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
            resolved[k] = random.uniform(v[0], v[1])
        else:
            resolved[k] = v
    return resolved


def _require_xai_key() -> str:
    key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not key:
        raise RuntimeError(
            "XAI_API_KEY missing. Use box env var XAI_API_KEY "
            "(documented in /workspace/shared/INVENTORY/accounts-subs-apis.md). "
            "Do not invent a new key."
        )
    return key


def call_model(
    alias: str,
    system_prompt: str,
    user_prompt: str,
    reasoning: bool = False,
    max_tokens: int | None = None,
    json_mode: bool = True,
    step: str = "call",
    show_id: str | None = None,
) -> str:
    if alias not in MODELS:
        raise ValueError(f"Unknown model alias: {alias}")
    config = _resolve_params(MODELS[alias])
    if config.get("provider") not in (None, "xai"):
        raise RuntimeError(
            f"Provider {config.get('provider')!r} disabled — Story Bot is Grok/xAI only"
        )
    ceiling = config.get("max_tokens_ceiling", config["max_tokens"])
    token_budget = min(max_tokens, ceiling) if max_tokens else config["max_tokens"]
    check_can_spend(est_usd=0.15)

    client = openai.OpenAI(api_key=_require_xai_key(), base_url=XAI_BASE_URL)
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    # reasoning flag unused on non-reasoning models; ignore quietly
    _ = reasoning

    attempt_budget = token_budget
    while True:
        try:
            response = client.chat.completions.create(
                model=config["model"],
                max_tokens=attempt_budget,
                temperature=config["temperature"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **kwargs,
            )
        except SpendLimitError:
            raise
        except Exception as e:
            raise RuntimeError(f"xAI API error ({alias}): {e}") from e

        usage = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        cost = estimate_cost(config["model"], prompt_tokens, completion_tokens)
        log_call(
            model=config["model"],
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            step=step,
            show_id=show_id,
        )
        print(
            f"[{alias}/{config['model']}] step={step} "
            f"prompt={prompt_tokens} completion={completion_tokens} cost=${cost:.6f}",
            flush=True,
        )

        choice = response.choices[0]
        if choice.finish_reason != "length":
            content = choice.message.content
            if not content:
                raise RuntimeError(
                    f"{alias} returned empty response (finish_reason={choice.finish_reason!r})"
                )
            return content

        if attempt_budget >= ceiling:
            break
        next_budget = min(attempt_budget * 2, ceiling)
        print(
            f"[{alias}] truncated at max_tokens={attempt_budget}, retrying {next_budget}",
            flush=True,
        )
        attempt_budget = next_budget

    raise RuntimeError(
        f"{alias} truncated (finish_reason='length') after ceiling {ceiling}"
    )
