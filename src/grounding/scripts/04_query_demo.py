"""
Script to demonstrate end-to-end hybrid retrieval with reranking.
Usage: python src/grounding/scripts/04_query_demo.py "your query here"
"""
import json
import logging
import sys
from pprint import pprint

from src.grounding.config import get_settings
from src.grounding.query.retriever import retrieve_adk_evidence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "How do I implement tool context in a python agent?"
        print(f"No query provided, using default: '{query}'")

    print(f"\nSearching for: {query}")
    print("=" * 60)

    try:
        result = retrieve_adk_evidence(
            query=query,
            mode="build", 
            top_k_final=5  # Small limit for readable output
        )
        
        print("\n--- Evidence Pack Summary ---")
        print(f"Status: {result.get('status', 'success')}")
        print(f"Candidates Found (pre-rerank): {result['debug'].get('candidates_found')}")
        print(f"Docs/Code Coverage: {result['coverage']}")
        if result.get('warnings'):
            print(f"Warnings: {result['warnings']}")

        print("\n--- Top Evidence ---")
        for item in result['evidence']:
            print(f"\nRank {item['rank']} | Score: {item['rerank_score']:.4f} | {item['source_type']}")
            print(f"Citation: {item['citation']}")
            print("-" * 30)
            # Print first 200 chars of text
            text_preview = item.get('text', '')[:200].replace('\n', ' ')
            print(f"Text: {text_preview}...")

    except Exception as e:
        logger.exception("Retrieval failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
