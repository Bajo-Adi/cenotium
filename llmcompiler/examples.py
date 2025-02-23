"""Example usage of LLMCompiler for trip planning."""
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool

from llm_compiler import LLMCompiler

def simple_trip_example():
    """Example of a simple trip planning request."""
    compiler = LLMCompiler()  # No need to pass tools anymore
    query = """
    Plan a trip to Hawaii for 4 people:
    - Budget: $2000 per person
    - Duration: 7 nights
    - Focus on outdoor activities and local culture
    """
    
    print("\nSimple Trip Planning Example:")
    print(f"Query: {query}")
    compiler.run(query)

def complex_trip_example():
    """Example of a complex trip planning request."""
    compiler = LLMCompiler()  # No need to pass tools anymore
    query = """
    Objective: Plan a pleasurable Spring Break trip to Cabo for a group of 8, ensuring all expenses are under $1500 per person for 5 nights and 6 days.

    Key Details:
    - Destination: Cabo
    - Group Size: 8 people
    - Budget: $1500 per person
    - Duration: 5 nights, 6 days

    Break Down Tasks:
    - Research and secure affordable round-trip flights and accommodations within the budget.
    - Plan daily itineraries that balance relaxation and exploration, including activities accessible in Cabo.
    - Allocate the budget for meals, local transport, and entertainment.
    - Consider group preferences and prioritize popular attractions or events in the area.

    Deliver a Plan:
    - Establish a consolidated budget outline to divide expenses efficiently.
    - Propose an itinerary with suggested activities and dining options, accounting for group interests.
    - Ensure all bookings (flights, accommodations) are confirmed in advance to avoid last-minute cost surges.
    - Regularly review and update plans as necessary.
    """
    
    print("\nComplex Trip Planning Example:")
    print(f"Query: {query}")
    compiler.run(query)

def multi_destination_example():
    """Example of planning a multi-destination trip."""
    compiler = LLMCompiler()  # No need to pass tools anymore
    query = """
    Plan a 2-week Europe trip covering:
    - Paris (4 nights)
    - Rome (5 nights)
    - Barcelona (5 nights)
    
    For 2 people with a budget of $5000 per person.
    Focus on cultural experiences and local cuisine.
    """
    
    print("\nMulti-destination Trip Planning Example:")
    print(f"Query: {query}")
    compiler.run(query)

if __name__ == "__main__":
    print("Running Trip Planning Examples with LLMCompiler...")
    
    # Run examples
    simple_trip_example()
    complex_trip_example()
    multi_destination_example()