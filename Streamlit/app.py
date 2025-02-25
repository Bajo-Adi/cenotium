import streamlit as st
from streamlit_option_menu import option_menu
import base64

def set_custom_css():
    st.markdown("""
        <style>
            body, p, li {
                font-size: 20px !important;
            }
            h1 {
                font-size: 34px !important;
            }
            h2 {
                font-size: 28px !important;
            }
            h3 {
                font-size: 24px !important;
            }
        </style>
    """, unsafe_allow_html=True)


def get_base64(image_path):
    """Convert an image to base64 encoding for embedding in HTML."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        st.error("Error: Image file not found. Please check the file path.")
        return None


def home():
    st.markdown(
        """
        <h1 style="text-align: center;">Cenotium: World's First Agentic Internet Browser</h1>


        """,
        unsafe_allow_html=True
    )

    image_path = "Streamlit/graphviz (6).png"
    
    image_base64 = get_base64(image_path)

    # If image conversion was successful, display it
    if image_base64:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{image_base64}" width="700">
                <p><em>Agentic Internet</em></p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("Failed to load image. Please check the file path and try again.")


    st.write("""
    The internet is evolving into a dynamic ecosystem where AI agents operate independently, transforming the way tasks are executed, decisions are made, and digital interactions take place. This Agentic Internet is not just an upgrade to the current web—it is a fundamental shift toward a world where autonomous agents handle information retrieval, transactions, security, and complex problem-solving with minimal human input.

However, today’s websites are built for human users, not AI agents. They rely on graphical interfaces, manual navigation, and scattered data structures that make it difficult for autonomous systems to interact efficiently. AI agents struggle to extract, interpret, and execute actions on traditional web pages, limiting their potential. To unlock the true power of an agent-driven web, the internet itself must evolve. We have built a browser designed exclusively for AI agents, reimagining the way they access and interact with online information. By structuring websites into agent-readable schemas, we enable seamless automation, decision-making, and task execution—paving the way for a new digital landscape optimized for AI autonomy.

This transformation demands a robust framework that supports agent-to-agent interactions, enforces trust mechanisms, and safeguards the integrity of the ecosystem. In the sections ahead, we will explore the key components that power this next-generation internet—how it is structured, how agents are managed, and how we ensure security and trust in a world where machines, not humans, take the lead.
    """)

    url = "https://devpost.com/software/cenotium?ref_content=my-projects-tab&ref_feature=my_projects"
    st.write("[Devpost](%s)" % url)

    url = "https://github.com/abhipi/cenotium"
    st.write("[Github](%s)" % url)

def scraper_page():
    st.markdown(
        """
        <h1 style="text-align: center;">Scraper and Web Schema Development</h1>
        """,
        unsafe_allow_html=True
    )
    st.write("""
    The current internet is fundamentally **not designed for AI agents**. Websites are built to be navigated and interacted with by humans, not autonomous systems. Unlike structured APIs that facilitate machine-to-machine communication, most websites rely on **front-end libraries like React, Angular, and Vue** to render their content dynamically. This means that **all interactable elements exist within the UI**, making them inaccessible to AI agents that lack a structured way to interpret and interact with them.
    
    For AI agents to function autonomously on the web, they require structured interfaces—**APIs that allow them to query, retrieve, and manipulate data programmatically**. However, the vast majority of websites **do not expose such APIs**, making it **impossible for agents to interact** with these sites as they would with structured databases or API-driven platforms. This presents a major challenge: if we do not find a way to bridge this gap, **agents will be unable to leverage the vast amount of data available on the internet**, leading to significant losses in usability and automation potential.
    """)
    
    st.markdown("""<h2 style="text-align: center;">Building a New Interaction Layer for Agents</h2>""", unsafe_allow_html=True)
    st.write("""
    To solve this, we have created a **custom schema layer** that acts as an **agent-accessible abstraction of the internet**. This layer **transforms standard web pages into structured, interactable formats** that AI agents can understand and engage with. Our approach is built upon three key AI-driven models:
    """)

    st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://osatlas.github.io/static/images/Intro.png" style="max-width: 90%; height: auto;">
        <p><em>OS-Atlas</em></p>
    </div>
    """,
    unsafe_allow_html=True
)


    st.subheader("1. Planning Model (Identifying Interactable Elements)")
    st.write("""
    The **Planning Model** leverages **vision-based AI models** to scan a web page and **identify interactive elements** that an agent may need to engage with. This includes:
    - **Buttons** (e.g., "Submit", "Add to Cart", "Login")
    - **Forms and Input Fields** (e.g., search bars, login credentials)
    - **Dynamic Elements** (e.g., dropdown menus, checkboxes, sliders)
    
    This model essentially **breaks down the structure of a webpage visually**, recognizing which parts are essential for task execution and navigation.
    """)
    
    st.subheader("2. Grounding Model (Mapping Interaction Coordinates)")
    st.write("""
    Once the interactable elements are identified, the **Grounding Model** assigns them precise **spatial coordinates** on the webpage. This is done using **OS-Atlas**, a foundational vision model that enables AI to localize and categorize objects in an environment.
    
    **What is OS-Atlas?**
    OS-Atlas is a **spatially-aware AI model** designed to create a reference map of digital environments. It works by:
    - **Detecting all elements on a webpage**
    - **Creating bounding boxes** around interactable elements
    - **Storing these bounding boxes for future visits**
    
    By persisting bounding boxes in a **Supabase database**, we ensure that **subsequent visits to the same website require fewer model calls**. Over time, the system becomes **more efficient and cost-effective**, as the model only needs to retrieve previously identified interaction points rather than reprocessing an entire page.
    """)
    
    st.markdown(
        """
        <div style="text-align: center;">
            <img src="https://d3lkc3n5th01x7.cloudfront.net/wp-content/uploads/2024/07/18011105/AI-Agents-for-Content-Generation-Banner.png" style="max-width: 90%; height: auto;">
            <p><em>Web Based Agents</em></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("3. Action Model (Enabling Agent Interactions)")
    st.write("""
    The **Action Model** consists of the **AI agents themselves**, which interact with the bounding boxes identified by the Grounding Model. These agents operate much like human users, clicking buttons, filling out forms, and navigating dynamically generated content.
    
    By **separating the identification, localization, and interaction processes**, we create a highly **scalable and efficient method** for agents to engage with the internet.
    """)
    
    st.markdown("""<h2 style="text-align: center;">Web Scraping and Contextual Data Storage</h2>""", unsafe_allow_html=True)
    st.write("""
    To further enhance the agentic web experience, we have developed a **custom scraper** built using:
    - **Selenium** (for controlled web navigation)
    - **OpenAI’s 4o-mini model** (for generating contextual descriptions of web elements)
    
    This scraper **extracts the raw HTML structure of websites** while also **downloading images** for further processing. These images are then **analyzed using vision models** to generate textual descriptions, which provide additional **context for the Planning, Grounding, and Action models**.
    
    All extracted data—including **HTML, images, descriptions, and bounding box coordinates**—is stored in **Supabase**, ensuring that agents can efficiently access structured representations of websites without needing to reprocess pages on every visit.
    """)

    image_path = "Streamlit/Supabase.png"
    
    image_base64 = get_base64(image_path)

    # If image conversion was successful, display it
    if image_base64:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{image_base64}" width="1000">
                <p><em>Supabase Database</em></p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("Failed to load image. Please check the file path and try again.")
    
    st.markdown("""<h2 style="text-align: center;">Why This Approach Works</h2>""", unsafe_allow_html=True)
    st.write("""
    1. **Preserving Internet Data:** Instead of replacing the traditional internet with a new ecosystem, we create a structured **overlay** that makes existing websites compatible with AI agents.
    2. **Scalability and Efficiency:** By storing interaction maps and reducing redundant model calls, our system **becomes faster and cheaper** over time.
    3. **Seamless AI Integration:** With structured schema-based interaction, agents can now **autonomously browse, transact, and retrieve information**, bringing the true potential of an **Agentic Internet** to life.
    
    This transformation **bridges the gap between human-driven and AI-driven web interaction**, ensuring that the future of the internet is not just navigable for people—but for autonomous agents as well.
    """)


def agents_page():
    st.markdown("""
    <h1 style="text-align: center;">Agents and the Agent Manager: Architecting an Autonomous Multi-Agent System</h1>
    """, unsafe_allow_html=True)

    image_path = "Streamlit/WhatsApp Image 2025-02-23 at 08.57.33.jpeg"
    
    image_base64 = get_base64(image_path)

    # If image conversion was successful, display it
    if image_base64:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{image_base64}" width="1000">
                <p><em>Agent Execution</em></p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("Failed to load image. Please check the file path and try again.")
    
    st.write("""
    The **Agent Manager** is the central intelligence hub responsible for receiving user prompts, interpreting them in context, and orchestrating a network of AI-powered agents to autonomously execute tasks. Rather than simply passing the user’s input to predefined functions, the manager enhances, structures, and strategically decomposes the request using an advanced **LLM Compiler**, ensuring optimal task execution.
    """)
    
    st.subheader("""Step 1: Understanding and Enhancing the User Prompt""")
    st.write("""
    When a user provides a prompt, it is first processed by the **Agent Compiler**, an intelligent module powered by **LLM Compiler**. This compiler contextualizes the prompt using historical user data stored in a **Knowledge Graph**.""")

    image_path = "Streamlit/graph.png"
    
    image_base64 = get_base64(image_path)

    # If image conversion was successful, display it
    if image_base64:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{image_base64}" width="500">
                <p><em>Knowledge Graph</em></p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("Failed to load image. Please check the file path and try again.")
    
    st.write("""
    ### Context Injection via a Knowledge Graph
    Unlike traditional AI systems that respond in isolation, our **Agent Manager** maintains a **persistent user representation** that dynamically evolves, storing:
    - **User preferences** (e.g., preferred airlines, frequently visited websites)
    - **Past interactions and workflows**
    - **Long-term goals and recurring requests**
    
    Each new prompt retrieves relevant context via **Retrieval-Augmented Generation (RAG)**, allowing the system to personalize the prompt. This ensures repeated tasks are streamlined, making the AI function as an **adaptive assistant** rather than a stateless chatbot.
    
    Example:
    If a user asks, *"Find me a flight to New York,"* the system retrieves their past searches and preferences, automatically refining the query to:
    *"Find me a flight to New York with Delta Airlines under $500, departing after 6 PM."*
    
    This refined prompt is then passed to **LLMs**, which decomposes it into structured, executable tasks for various agents.
    """)
    
    st.subheader("""Step 2: Planning and Re-Planning Task Execution""")
    st.write("""
    The **Agent Manager** invokes **Planning & Replanning mechanisms** using **ChatGPT-4o, DeepSeek R1 and Claude 3.5 Sonnet**, breaking down the user’s request into a structured execution plan:
    - **Primary Planning** → Initial breakdown into discrete subtasks.
    - **Agent Selection** → Assigning each subtask to an appropriate agent.
    - **Replanning Mechanism** → If an agent encounters an issue (e.g., an outdated search result), the system dynamically **replans the execution path**.
    
    This structured approach ensures complex, multi-step operations like booking a flight, automating a workflow, or gathering research are handled **autonomously and efficiently**.
    """)

    image_path = "Streamlit/WhatsApp Image 2025-02-23 at 09.10.46.jpeg"
    
    image_base64 = get_base64(image_path)

    # If image conversion was successful, display it
    if image_base64:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{image_base64}" width="750">
                <p><em>Multi-Agent output streaming</em></p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("Failed to load image. Please check the file path and try again.")
    
    st.subheader("""Step 3: Agent Activation and Execution""")
    st.write("""
    Each task is delegated to an **AI-powered agent**, structured as a **LangChain Tool Agent**. The system is **infinitely expandable**, meaning any AI-powered tool can be integrated to increase functionality. Current agents include:
    """)
    
    st.subheader("1. Perplexity Search Agent (General-Purpose Knowledge Retrieval)")
    st.write("""
    - Executes **real-time web searches** to gather additional information.
    - Retrieves **factual and contextual knowledge** from online sources.
    - Serves as a **query engine** for other agents needing additional insights.
    """)
    
    st.subheader("2. Twilio Calling Agent (Automated Communication)")
    st.write("""
    - Places **automated outbound calls** and delivers AI-generated messages.
    - Processes **inbound responses**, integrating real-time updates into execution workflows.
    """)
    
    st.subheader("3. Browser Activation Agent (Web Interaction & Automation)")
    st.write("""
    - Simulates a **user browsing session**, interacting dynamically with web pages.
    - Detects **UI elements** like buttons, forms, and text fields.
    - **Autonomously navigates**, submits forms, and retrieves data from web applications.
    - Utilizes E2B.dev containerized environments with OS Atlas grounding and GPT-4o planning to interact with web elements, executing tasks via a Poetry-managed Python stack with PyQt5, Flask, OpenCV, and FFmpeg integration.
    """)

    st.subheader("""Step 4: Continuous Execution and Thought Streaming""")
    st.write("""
    The **Agent Manager maintains a real-time chain of thought**, continuously adapting as new information arises. This allows for:
    - **Streaming execution logs** for user transparency.
    - **Dynamic modification of execution paths** when encountering issues.
    - **Real-time agent collaboration**, where multiple agents work in parallel.
    
    Example:
    While the **Browser Activation Agent** fills out a form, the **Perplexity Search Agent** might simultaneously **fetch additional details** to ensure input accuracy.
    """)
    
    st.subheader("""The Future: A Limitless Multi-Agent Ecosystem""")
    st.write("""
    The **Agent Manager** currently hosts **three core agents**, but the architecture supports **infinite expansion**. Future integrations include:
    - **Automated Email & Calendar Agents** for scheduling and communication.
    - **AI-Powered Research Assistants** that analyze academic papers.
    - **E-commerce Bots** that autonomously find and purchase products.
    - **Legal & Financial Agents** for contract analysis and investment recommendations.
    
    By creating an **open, modular system**, we lay the foundation for a **fully autonomous, AI-driven internet**, where agents self-improve, collaborate, and expand their capabilities over time.
    """)
def security_page():
    st.markdown("""
    <h1 style="text-align: center;">Security, Trust, and Reliability in the Agentic Internet</h1>
    """, unsafe_allow_html=True)
    
    st.write("""
    Ensuring security, trust, and efficient inter-agent communication is critical in the **Agentic Internet**. To achieve this, we implement a **multi-layered security framework** that manages agent reputation, enforces encryption, and optimizes trust propagation using modified **EigenTrust and PageRank** algorithms. 
    
    Our security infrastructure is designed to handle **agent-to-agent interactions, data integrity, and trust validation** at a large scale. By combining **encryption, trust scoring, and performance metrics**, we ensure a **safe, self-improving agent network** that operates efficiently.
    """)
    
    st.markdown("""<h2 style="text-align: center;">Trust and Reputation System</h2>""", unsafe_allow_html=True)
    st.write("""
    The **Trust Core** dynamically ranks and evaluates agent reliability based on past transactions. This ensures that only **trusted agents** execute critical tasks. Our system is based on **EigenTrust for P2P Networks**, which propagates **trust scores across the network** while considering **multi-factor evaluations** such as:
    - **Local Trust** → Direct agent-to-agent interactions based on successful task completion.
    - **Global Trust** → Aggregates trust across multiple interactions and agents, ensuring **trust propagation**.
    - **Temporal Decay** → More recent transactions **carry higher weight**, ensuring trust scores evolve dynamically.
    - **Performance Factors** → Evaluates **task complexity, response time, and historical reliability**.
    
    This system ensures **trust convergence**, meaning additional transactions **refine** the trust scores rather than introduce instability. 
    """)
    
    st.markdown("""<h3 style="text-align: center;">Trust Calculation Example</h3>""", unsafe_allow_html=True)
    st.code("""
    transactions = [
        {'agent_id': 'A1', 'timestamp': datetime(2024, 2, 20), 'success': True, 'response_time': 0.5, 'complexity': 0.8},
        {'agent_id': 'A2', 'timestamp': datetime(2024, 2, 21), 'success': False, 'response_time': 2.0, 'complexity': 0.4}
    ]
    
    # Apply Temporal Decay
    weight_A1 = 0.95  # Older transaction
    weight_A2 = 1.0  # Recent transaction
    
    # Compute Local Trust
    A1_trust = (1.0 * 0.95) / 0.95  # = 1.0
    A2_trust = (0.0 * 1.0) / 1.0  # = 0.0
    
    # Compute Global Trust
    A1_global = 0.85 * A1_trust + 0.15 * (neighbor_scores)
    A2_global = 0.85 * A2_trust + 0.15 * (neighbor_scores)
    """, language="python")
    
    st.markdown("""<h3 style="text-align: center;">Modified EigenTrust + PageRank Formula</h3>""", unsafe_allow_html=True)
    st.markdown("""
    **Final Trust Calculation Formula:**
    """)
    
    st.success("""
    final_trust = α * local_trust + (1 - α) * global_trust
    """
    )
    
    st.markdown("""<h2 style="text-align: center;">Security Protocols and Data Protection</h2>""", unsafe_allow_html=True)
    st.write("""
    To protect communication between agents and prevent breaches, we utilize:
    - **Fernet Symmetric Encryption** → Ensures **secure message transmission** using **AES in CBC mode** with **HMAC-SHA256 authentication**.
    - **Rate Limiting & Digital Signatures** → Prevents abuse by limiting excessive interactions and verifying agent authenticity.
    - **In-Memory Pseudo-Database** → Maintains **contextual trust records** to improve agent reliability and prevent malicious actions.
    
    This encryption and verification framework ensures that **agent interactions remain secure, authenticated, and resilient against attacks**.
    """)
    
    st.markdown("""<h2 style="text-align: center;">Inter-Agent Communication & Messaging Security</h2>""", unsafe_allow_html=True)
    st.write("""
    Agents communicate via a **Custom Inter-Agent Communication Protocol**, inspired by **RabbitMQ/Kafka**, ensuring:
    - **Topic-Based Routing** → Messages are directed efficiently to the appropriate agent.
    - **Asynchronous Processing** → Enables **scalable, real-time execution** via **in-memory priority queues**.
    - **End-to-End Encryption** → Secures all communications to prevent unauthorized access.
    
    This protocol ensures **efficient, secure, and scalable message passing**, enabling large-scale **agent collaboration and coordination**.
    """)
    
    st.markdown("""<h2 style="text-align: center;">Persistent Storage and Performance Optimization</h2>""", unsafe_allow_html=True)
    st.write("""
    - **Redis** is used for caching **frequently accessed agent interactions**, ensuring low-latency retrieval and efficient execution.
    - **Supabase** stores structured **agent schemas, interaction logs, and trust scores**, providing scalable and reliable data storage.
    - **Transaction Performance Metrics** → Systematically evaluates **latency, execution success rates, and resource efficiency**, helping refine agent interactions.
    
    Our **security architecture** ensures a **robust, self-improving AI-driven network**, where agents operate autonomously **while maintaining system integrity and trust enforcement**.
    """)


def main():
    st.set_page_config(layout="wide")
    set_custom_css()
    
    with st.sidebar:
        selected = option_menu("Menu", ["Home", "Web Schema", "Agents and Agent Manager", "Security and Trust"], 
                               icons=["house", "search", "robot", "shield", "palette"],
                               menu_icon="menu-hamburger", default_index=0)
    
    if selected == "Home":
        home()
    elif selected == "Web Schema":
        scraper_page()
    elif selected == "Agents and Agent Manager":
        agents_page()
    elif selected == "Security and Trust":
        security_page()
    
if __name__ == "__main__":
    main()
