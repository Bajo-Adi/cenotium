import os
import logging
from pathlib import Path

# Import the nano_graphrag package from GitHub dependency
from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag._storage import Neo4jStorage

from neo4j_vis import visualize_neo4j_graph

# Configure logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("nano-graphrag").setLevel(logging.INFO)

# Set your OpenAI API Key (replace with your key)
os.environ["OPENAI_API_KEY"] = "your_openai_api_key_here"

# Define your Neo4j configuration using a direct Bolt connection.
neo4j_config = {
    "neo4j_url": os.environ.get("NEO4J_URL", "bolt://localhost:7690"),
    "neo4j_auth": (
        os.environ.get("NEO4J_USER", "neo4j"),
        os.environ.get("NEO4J_PASSWORD", "shrey1306"),
    ),
}

# Initialize GraphRAG with Neo4j storage
graph_func = GraphRAG(
    graph_storage_cls=Neo4jStorage,
    addon_params=neo4j_config,
    working_dir="./cenotium",  # Directory for storing working files
)

def insert_and_visualize(file_path, vis_output):
    """
    Insert content from a text file into the graph and visualize it.
    
    Args:
        file_path (str): Path to the text file.
        vis_output (str): Path where the HTML visualization will be saved.
    """
    with open(file_path, 'r') as file:
        content = file.read()
        graph_func.insert(content)
    visualize_neo4j_graph(output_file=vis_output)

def process_user_profiles(input_dir, output_dir):
    """
    Process all .txt files in the input directory and generate graph visualizations.
    
    Args:
        input_dir (str): Directory containing input text files.
        output_dir (str): Directory to save visualization HTML files.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for txt_file in Path(input_dir).glob('*.txt'):
        output_file = Path(output_dir) / f"{txt_file.stem}_graph.html"
        try:
            insert_and_visualize(str(txt_file), str(output_file))
            print(f"Successfully processed {txt_file.name}")
        except Exception as e:
            print(f"Error processing {txt_file.name}: {e}")

def run_query(user_prompt):
    """
    Appends a fixed suffix to the user prompt and performs a local GraphRAG query.
    
    Args:
        user_prompt (str): The prompt entered by the user.
    
    Returns:
        The query response from GraphRAG.
    """
    final_prompt = user_prompt + '''
Based on the user's memory and the prompt; Summarize the Objective:
Clearly restate the main goal and constraints.

Identify Key Details:
Extract critical information such as group size, budget, duration, and destination.

Break Down Tasks:
Outline clear, actionable steps for the team (e.g., budgeting, itinerary planning, activity suggestions, and logistics).

Deliver a Plan:
Present a concise, step-by-step plan with measurable outcomes.

Keep it minimally objective, and the response short in 5-6 bullet points'''
    response = graph_func.query(final_prompt, param=QueryParam(mode="local"))
    return response

if __name__ == "__main__":
    # (Optional) Process user profile files for visualization
    input_directory = "user_profiles"  # Folder with your .txt files
    output_directory = "user_memory/user_graphs"
    process_user_profiles(input_directory, output_directory)

    # Example run: query using a user input prompt
    sample_prompt = ("We are a group of 8 going to Cabo for Spring Break. "
                     "Our budget is $1500 per person and we're going for 5N, 6D")
    result = run_query(sample_prompt)
    print("Query Response:", result)
