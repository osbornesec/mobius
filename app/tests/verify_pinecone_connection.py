#!/usr/bin/env python3
"""
Quick script to verify Pinecone connection and API key.
Run this before running the full test suite.
"""

import os
import sys
from pinecone import Pinecone


def verify_pinecone_connection():
    """Verify Pinecone API connection."""
    # Check for API key
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("❌ PINECONE_API_KEY environment variable not set!")
        print("   Set it with: export PINECONE_API_KEY='your-api-key-here'")
        return False

    print("✓ PINECONE_API_KEY found")

    try:
        # Initialize client
        pc = Pinecone(api_key=api_key)
        print("✓ Pinecone client initialized")

        # List indexes
        indexes = pc.list_indexes()
        print("✓ Successfully connected to Pinecone")
        print(f"  Found {len(indexes)} existing indexes")

        # Show existing indexes
        if indexes:
            print("  Existing indexes:")
            for idx in indexes:
                print(
                    f"    - {idx.name} (dimension: {idx.dimension}, metric: {idx.metric})"
                )

        # Check if test index exists
        test_index_name = "mobius-test-index"
        if test_index_name in [idx.name for idx in indexes]:
            print(f"\n⚠️  Warning: Test index '{test_index_name}' already exists.")
            print("   The test suite will attempt to delete and recreate it.")

        print("\n✅ Pinecone connection verified! You can run the tests now.")
        return True

    except Exception as e:
        print(f"\n❌ Failed to connect to Pinecone: {str(e)}")
        print("\nPossible issues:")
        print("  - Invalid API key")
        print("  - Network connectivity issues")
        print("  - Pinecone service issues")
        return False


if __name__ == "__main__":
    success = verify_pinecone_connection()
    sys.exit(0 if success else 1)
