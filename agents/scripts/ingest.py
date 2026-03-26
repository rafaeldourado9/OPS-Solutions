#!/usr/bin/env python
"""
CLI script for ingesting company documents into the Qdrant RAG collection.

Usage:
    # Ingest all docs for an agent (looks in agents/{agent}/docs/)
    python scripts/ingest.py --agent empresa_x

    # Ingest a specific file
    python scripts/ingest.py --agent empresa_x --file path/to/manual.pdf

    # Ingest a specific directory
    python scripts/ingest.py --agent empresa_x --dir path/to/docs/

    # Custom chunking parameters
    python scripts/ingest.py --agent empresa_x --chunk-size 800 --overlap 100

Environment variables required:
    QDRANT_URL, OLLAMA_URL (see .env.example)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure the project root is on sys.path when running as a script
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from adapters.outbound.memory.qdrant_adapter import QdrantAdapter
from core.use_cases.ingest_documents import IngestDocumentsUseCase, SUPPORTED_EXTENSIONS
from infrastructure.config_loader import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


async def run(args: argparse.Namespace) -> None:
    agent_id: str = args.agent

    # Load agent config
    config = get_config(agent_id)
    logger.info(
        "Agent: %s (%s) — LLM: %s/%s",
        config.agent.name,
        config.agent.company,
        config.llm.provider,
        config.llm.model,
    )

    # Build Qdrant adapter and ensure collections exist
    qdrant = QdrantAdapter(
        chat_collection=config.memory.qdrant_collection,
        rules_collection=config.memory.qdrant_rag_collection,
        embedding_model=config.memory.embedding_model,
    )
    await qdrant.ensure_collections()

    # Build use case
    uc = IngestDocumentsUseCase(qdrant=qdrant, config=config)

    # Determine what to ingest
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            sys.exit(1)
        total = await uc.ingest_file(
            file_path,
            agent_id=agent_id,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
    else:
        if args.dir:
            dir_path = Path(args.dir)
        else:
            dir_path = _project_root / "agents" / agent_id / "docs"

        if not dir_path.exists():
            logger.error("Directory not found: %s", dir_path)
            logger.info(
                "Place your documents in agents/%s/docs/ or use --dir to specify a path.",
                agent_id,
            )
            sys.exit(1)

        total = await uc.ingest_directory(
            dir_path,
            agent_id=agent_id,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )

    await qdrant.close()

    print(f"\n✓ Ingestion complete: {total} chunk(s) stored for agent '{agent_id}'")
    print(f"  Collection: {config.memory.qdrant_rag_collection}")
    print(f"  Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest company documents into the RAG collection for a WhatsApp agent.",
    )
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent ID (must match a folder in agents/)",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Single file to ingest (PDF, DOCX, TXT, or image)",
    )
    parser.add_argument(
        "--dir",
        default=None,
        help="Directory to ingest (defaults to agents/{agent}/docs/)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        dest="chunk_size",
        help="Target characters per chunk (default: 500)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=60,
        help="Overlap characters between chunks (default: 60)",
    )

    args = parser.parse_args()

    if args.file and args.dir:
        parser.error("Use either --file or --dir, not both.")

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
