"""Example script to demonstrate how to use the supervisor."""

import asyncio
import json
from langchain_core.messages import HumanMessage

from src.supervisor import SupervisorAgent


async def main():
    """Run the example."""
    # Initialize the supervisor
    supervisor = SupervisorAgent()
    
    # Example queries for different agents
    queries = [
        "I need a romantic script for a date night with my partner. We want something playful and fun.",
        "I need to design a box for shipping fragile items. It should be 30cm x 20cm x 15cm.",
        "Can you research the history of artificial intelligence and provide a summary?",
    ]
    
    # Process each query
    for query in queries:
        print(f"\n\n{'=' * 50}")
        print(f"QUERY: {query}")
        print(f"{'=' * 50}\n")
        
        # Create a human message
        message = HumanMessage(content=query)
        
        # Invoke the supervisor
        result = await supervisor.invoke([message])
        
        # Print the result
        last_message = result.messages[-1]
        print(f"AGENT: {result.current_agent}")
        
        try:
            # Try to parse the response as JSON
            content = json.loads(last_message.content)
            if isinstance(content, dict):
                if "final_script" in content:
                    print(f"RESPONSE: {content['final_script']}")
                elif "final_design" in content:
                    print(f"RESPONSE: {content['final_design']}")
                elif "final_report" in content:
                    print(f"RESPONSE: {content['final_report']}")
                else:
                    print(f"RESPONSE: {last_message.content}")
            else:
                print(f"RESPONSE: {last_message.content}")
        except json.JSONDecodeError:
            print(f"RESPONSE: {last_message.content}")


if __name__ == "__main__":
    asyncio.run(main()) 