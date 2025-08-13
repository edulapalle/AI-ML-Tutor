#!/usr/bin/env python3
"""
Generate child-friendly ML/AI learning chunks (definitions, analogies, examples, mistakes,
mini-quizzes, related-concepts) for each concept in concepts.json and write to JSONL.

Output schema (one record per chunk):
{
  "id": "gradient-descent__analogy__s2__v1",
  "concept_slug": "gradient-descent",
  "concept_title": "Gradient Descent",
  "slice": "analogy",              # one of: definition|analogy|example|mistake|quiz|related
  "style": "sports",               # style hint for diversity
  "audience": "kid",
  "text": "... 120–180 words ...", # final chunk
  "tags": ["optimization","foundations"],
  "source": "self_generated_v1",
  "timestamp": "2025-08-10T19:35:00Z"
}

Run:
  $ export OPENAI_API_KEY=...
  $ python generate_dataset.py --concepts concepts.json --out ml_analogies.jsonl \
      --slices 6 --variants 4 --model gpt-4o-mini

Notes:
- Keeps temperature low for consistency (0.2)
- Retries with exponential backoff
- Resumable (skips ids already in output file)
- Designed to generate ~1,000+ chunks in ~30–90 mins depending on quotas
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

# OpenAI v1 client (pip install openai>=1.30.0)
from openai import OpenAI
from openai import RateLimitError, APIError, APIConnectionError

# Load environment variables and configure SSL
load_dotenv()

# Fix SSL certificates for Python (use system certificates)
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'

# -------------------------------
# Config
# -------------------------------

SLICE_TYPES = ["definition", "analogy", "example", "mistake", "quiz", "related"]
STYLE_HINTS = ["classroom", "sports", "cooking", "playground"]  # rotate for diversity
DEFAULT_TAGS_BY_SLICE = {
    "definition": ["definition", "kid-friendly"],
    "analogy": ["analogy", "story"],
    "example": ["example", "real-life"],
    "mistake": ["pitfall", "common-mistake"],
    "quiz": ["quiz", "check-understanding"],
    "related": ["related", "concept-map"]
}

SYSTEM_INSTRUCTION = (
    "You are a patient ML tutor for a 10-year-old. "
    "Use plain language, short sentences (8–14 words), and friendly tone. "
    "Avoid formulas and jargon unless absolutely needed. "
    "No harmful or sensitive content."
)

# Prompt templates for each slice
PROMPTS = {
    "definition": (
        "Explain the concept '{title}' for a 10-year-old in 3–4 short sentences. "
        "Avoid formulas. End with one sentence about when it is useful. "
        "Keep total length about 120–180 words."
    ),
    "analogy": (
        "Create a child-friendly analogy for '{title}' in {style} theme. "
        "Use 4–5 sentences and a concrete everyday situation. "
        "Keep total length about 120–180 words."
    ),
    "example": (
        "Give a real-life example where '{title}' is used, in 4–5 sentences. "
        "Make it easy for a 10-year-old to understand. "
        "Keep total length about 120–180 words."
    ),
    "mistake": (
        "Describe a common mistake when learning '{title}' and how to avoid it, "
        "in 4–5 kid-friendly sentences. "
        "Keep total length about 120–180 words."
    ),
    "quiz": (
        "Write one simple question about '{title}' and a short answer. "
        "Output exactly two lines starting with 'Q:' and 'A:'. "
        "Keep it child-friendly."
    ),
    "related": (
        "List 2–3 closely related ML concepts to '{title}'. "
        "For each, add one kid-friendly sentence explaining the relationship. "
        "Return 2–3 bullet points starting with '- '."
    ),
}

@dataclass
class Concept:
    slug: str
    title: str

# -------------------------------
# Utilities
# -------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def load_concepts(path: Path) -> List[Concept]:
    data = json.loads(path.read_text())
    concepts = []
    for item in data:
        slug = item.get("slug")
        title = item.get("title") or slug.replace("-", " ").title()
        concepts.append(Concept(slug=slug, title=title))
    return concepts

def existing_ids(out_path: Path) -> Set[str]:
    ids: Set[str] = set()
    if not out_path.exists():
        return ids
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if "id" in rec:
                    ids.add(rec["id"])
            except Exception:
                continue
    return ids

def write_jsonl(path: Path, records: List[Dict]):
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def chunk_id(concept_slug: str, slice_name: str, style: str, variant_idx: int) -> str:
    # stable id, versioned
    return f"{concept_slug}__{slice_name}__{style[:1]}{variant_idx}__v1"

def backoff_sleep(attempt: int):
    # exponential backoff with jitter
    base = min(2 ** attempt, 32)
    time.sleep(base + random.random())

# -------------------------------
# LLM call (OpenAI)
# -------------------------------

def make_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=api_key)

def call_llm(client: OpenAI, model: str, system: str, user: str, temperature: float = 0.2) -> str:
    """Synchronous, with retries."""
    for attempt in range(6):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            text = resp.choices[0].message.content.strip()
            return text
        except (RateLimitError, APIError, APIConnectionError) as e:
            if attempt >= 5:
                raise
            backoff_sleep(attempt)
    raise RuntimeError("LLM call failed after retries")

# -------------------------------
# Main generation loop
# -------------------------------

def gen_records_for_concept(
    client: OpenAI,
    concept: Concept,
    slices: List[str],
    variants_per_slice: int,
    model: str,
    audience: str = "kid",
) -> List[Dict]:
    out: List[Dict] = []
    for slice_name in slices:
        for v in range(variants_per_slice):
            style = random.choice(STYLE_HINTS)
            tmpl = PROMPTS[slice_name]
            prompt = tmpl.format(title=concept.title, style=style)

            text = call_llm(client, model=model, system=SYSTEM_INSTRUCTION, user=prompt, temperature=0.2)

            cid = chunk_id(concept.slug, slice_name, style, v + 1)
            rec = {
                "id": cid,
                "concept_slug": concept.slug,
                "concept_title": concept.title,
                "slice": slice_name,
                "style": style,
                "audience": audience,
                "text": text,
                "tags": DEFAULT_TAGS_BY_SLICE.get(slice_name, []),
                "source": "self_generated_v1",
                "timestamp": now_iso(),
            }
            out.append(rec)
    return out

def filter_and_trim(records: List[Dict]) -> List[Dict]:
    """Quick guardrails: length window + simple badword check (lightweight)."""
    badwords = {"sex", "violence", "drug"}  # placeholder; your moderation layer can be added later
    filtered: List[Dict] = []
    for r in records:
        t = r["text"]
        # length window: aim ~120–180 words (~800–1200 chars)
        wc = len(t.split())
        if r["slice"] in ("quiz", "related"):
            # short forms allowed
            if wc < 4 or wc > 120:
                continue
        else:
            if wc < 80 or wc > 220:
                continue

        lower = t.lower()
        if any(bw in lower for bw in badwords):
            continue

        filtered.append(r)
    return filtered

def dedupe(records: List[Dict]) -> List[Dict]:
    seen: Set[str] = set()
    out: List[Dict] = []
    for r in records:
        key = (r["concept_slug"], r["slice"], r["text"][:80].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concepts", type=str, default="concepts.json")
    ap.add_argument("--out", type=str, default="ml_analogies.jsonl")
    ap.add_argument("--model", type=str, default="gpt-4o-mini")
    ap.add_argument("--slices", type=int, default=6, help="number of slice types to use (max 6)")
    ap.add_argument("--variants", type=int, default=4, help="variants per slice per concept")
    ap.add_argument("--limit", type=int, default=0, help="limit number of concepts (0 = all)")
    args = ap.parse_args()

    out_path = Path(args.out)
    done_ids = existing_ids(out_path)

    concepts = load_concepts(Path(args.concepts))
    if args.limit > 0:
        concepts = concepts[: args.limit]

    # Decide which slice names we include (prefix of SLICE_TYPES)
    use_slices = SLICE_TYPES[: max(1, min(args.slices, len(SLICE_TYPES)))]

    print(f"Concepts: {len(concepts)} | slices: {use_slices} | variants/slice: {args.variants}")
    print(f"Resuming: {len(done_ids)} records already in {out_path}")

    client = make_openai_client()

    produced = 0
    for idx, c in enumerate(concepts, 1):
        print(f"[{idx}/{len(concepts)}] {c.slug} …")
        records = gen_records_for_concept(
            client=client,
            concept=c,
            slices=use_slices,
            variants_per_slice=args.variants,
            model=args.model,
        )

        # Filter & dedupe
        records = filter_and_trim(records)
        records = dedupe(records)

        # Skip ones already written (by id)
        new_records = [r for r in records if r["id"] not in done_ids]
        if not new_records:
            print("  → nothing new (all ids exist)")
            continue

        write_jsonl(out_path, new_records)
        for r in new_records:
            done_ids.add(r["id"])
        produced += len(new_records)
        print(f"  → wrote {len(new_records)} records (total so far: {produced})")

    print(f"Done. Wrote {produced} new records to {out_path}")

if __name__ == "__main__":
    main()
