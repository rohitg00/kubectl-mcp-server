#!/usr/bin/env python3
"""
Test script for kubectl-mcp-tool natural language processing.

This script tests the integration with a live Kubernetes cluster
by directly using the natural language processor.
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-test")

# Import from the kubectl_mcp_tool package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from kubectl_mcp_tool.natural_language import process_query

# Set mock mode to false for testing against the real cluster
os.environ["MCP_TEST_MOCK_MODE"] = "0"

async def test_natural_language_processing():
    """Test the natural language processing directly."""
    logger.info("Testing natural language processing with the live Kubernetes cluster")
    
    # Test a series of natural language queries
    test_queries = [
        "get pods",
        "get namespaces",
        "get nodes",
        "get deployments",
        "get services"
    ]
    
    for query in test_queries:
        logger.info(f"Processing query: {query}")
        result = process_query(query)
        print(f"\nQuery: {query}")
        print(f"Command: {result['command']}")
        print(f"Success: {result.get('success', False)}")
        print(f"Result:\n{result['result']}")
        print("-" * 50)
    
    logger.info("Natural language processing tests completed successfully")

async def main():
    """Main test function."""
    try:
        await test_natural_language_processing()
        logger.info("All tests completed successfully")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 