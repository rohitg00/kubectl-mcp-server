import sys
import json
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def test_query():
    """Test the kubectl-mcp natural language processing."""
    query = "list all pods in default namespace"
    print(f"Sending query: '{query}'")
    
    # Use stdio_client with StdioServerParameters
    server_params = StdioServerParameters(
        command="kubectl-mcp",
        args=["serve"],
    )
    
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the session
            await session.initialize()
            
            # Call the natural language processing tool
            result = await session.call_tool(
                "process_natural_language", 
                {"query": query}
            )
            
            # Extract the text content from the response
            if result.content and len(result.content) > 0:
                text_content = result.content[0].text
                # Parse the JSON response
                try:
                    parsed = json.loads(text_content)
                    print("\n=== COMMAND ===")
                    print(parsed["result"]["command"])
                    print("\n=== RESULT ===")
                    print(parsed["result"]["result"])
                    print("\n=== SUCCESS ===")
                    print(parsed["result"]["success"])
                except json.JSONDecodeError:
                    print("Could not parse JSON from response:", text_content)
                except KeyError as e:
                    print(f"Missing key in response: {e}")
                    print("Full response:", parsed)
            else:
                print("No content in response")

if __name__ == "__main__":
    asyncio.run(test_query())