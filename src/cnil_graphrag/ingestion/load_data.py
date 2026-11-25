"""Step 1 - Ingestion: load the CNIL dataset, clean it, filter it and save it as Parquet.

Outputs (in data/):
    sanctions_decisions.parquet  one row per decision (full text), for the LLM extraction
    sanctions_chunks.parquet     sanction chunks, for the classic RAG
    rules_chunks.parquet         CNIL rules chunks, for the vector search

Run from the project root:
    uv run python src/cnil_graphrag/ingestion/load_data.py
"""


from pathlib import Path

import pandas as pd
from datasets import load_dataset

# Project root = 3 folders above this file (ingestion -> cnil_graphrag -> src -> root)
DATA_DIR = Path(__file__).resolve().parents[3] / "data"

GDPR_START = "2018-05-25"
SANCTION_TYPES = ["Mise en demeure", "Sanction"]
RULE_TYPES = ["Recommandation/Lignes directrices", "Référentiel/Règlement type/Norme"]
MIN_CHUNK_LENGTH = 100  # shorter chunks are sentence fragments with no meaning on their own

# Rules useful for SMEs (out of 84 rules since 2018)
RULES_TO_KEEP = [
    "2020-091", "2020-092", "2025-131", "2026-042", "2026-114",
    "2019-160", "2022-126", "2026-031", "2026-054", "2023-064", "2019-001", "2025-028",
    "2022-100", "2025-019", "2021-122", "2023-050", "2026-022",
    "2018-326", "2018-327", "2019-011", "2019-118",
    "2021-131", "2021-130", "2018-303", "2021-057",
    "2025-024", "2024-011", "2025-010", "2025-041", "2025-047", "2024-041",
    "2026-063", "2021-043",
    "2020-081", "2022-067", "2020-076",
    "2021-070", "2026-045",
]

# Rules without content: annex missing from the dataset, or simple modifications
RULES_WITHOUT_CONTENT = [
    "2019-011", "2020-076", "2024-011", "2024-041", "2025-010",
    "2025-019", "2025-024", "2025-028", "2025-041", "2025-047",
    "2026-022", "2026-031", "2026-042", "2026-045", "2026-054",
    "2026-063", "2026-114",
]

COLS_TO_DROP = ["chunk_id", "chunk_xxh64", "nature", "status", "chunk_text", "embeddings_bge-m3"]


def load_raw() -> pd.DataFrame:
    """Download the CNIL dataset from Hugging Face."""
    ds = load_dataset("AgentPublic/cnil")
    return ds["train"].to_pandas()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Fix types and remove leading/trailing whitespace (e.g. '2026-022 ')."""
    df["date"] = pd.to_datetime(df["date"])
    df["number"] = df["number"].str.strip()
    df["full_title"] = df["full_title"].str.strip()
    df["year"] = df["date"].dt.year
    return df.drop(columns=COLS_TO_DROP)


def merge_chunks(chunks: pd.DataFrame) -> pd.DataFrame:
    """Sort chunks by position, then merge them into one row per decision."""
    chunks = chunks.sort_values(by=["doc_id", "chunk_index"])
    return chunks.groupby("doc_id").agg({
        "nature_delib": "first",
        "title": "first",
        "full_title": "first",
        "number": "first",
        "date": "first",
        "text": " ".join,
        "year": "first",
    }).reset_index()


def build_sanctions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (decisions, chunks) for sanctions and mises en demeure since the GDPR."""
    chunks = df[(df["nature_delib"].isin(SANCTION_TYPES)) & (df["date"] >= GDPR_START)].copy()

    # One row per decision, without the closure letters (no useful content)
    decisions = merge_chunks(chunks)
    decisions = decisions[~decisions["text"].str.contains("clôture du dossier")]
    
    # Chunks: remove sentence fragments and closure letters
    chunks = chunks[chunks["text"].str.len() >= MIN_CHUNK_LENGTH]
    chunks = chunks[chunks["doc_id"].isin(decisions["doc_id"])].copy()

    return decisions, chunks

def build_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Return the chunks of the CNIL rules useful for SMEs and with real content."""
    rules = df[(df["nature_delib"].isin(RULE_TYPES)) & (df["date"] >= GDPR_START)]
    rules = rules[rules["number"].isin(RULES_TO_KEEP)]
    rules = rules[~rules["number"].isin(RULES_WITHOUT_CONTENT)]
    return rules.sort_values(by=["doc_id", "chunk_index"]).copy()


def save(df: pd.DataFrame, name: str) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(DATA_DIR / name, index=False)


def main() -> None:
    df = clean(load_raw())

    decisions, sanction_chunks = build_sanctions(df)
    rules = build_rules(df)

    save(decisions, "sanctions_decisions.parquet")
    save(sanction_chunks, "sanctions_chunks.parquet")
    save(rules, "rules_chunks.parquet")

    print(f"{len(decisions)} decisions, {len(sanction_chunks)} sanction chunks, "
          f"{rules['doc_id'].nunique()} rules -> saved in {DATA_DIR}")


if __name__ == "__main__":
    main()