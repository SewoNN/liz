# LangGraph Supervisor with ReAct Agents

This repository demonstrates a supervisor architecture with multiple specialized ReAct agents implemented using [LangGraph](https://github.com/langchain-ai/langgraph).

## Architecture

The system consists of:

1. **Supervisor Agent**: Coordinates multiple specialized agents, analyzes user requests, and routes them to the appropriate agent.

2. **Specialized ReAct Agents**:
   - **Script Maker Agent**: Generates creative scripts based on user input.
   - **Box Maker Agent**: Creates box designs based on user specifications.
   - **Research Agent**: Gathers and analyzes information based on user queries.

3. **Base Agent Framework**: A common foundation for all agents, providing shared functionality and structure.

## How It Works

1. The user sends a request to the Supervisor Agent.
2. The Supervisor analyzes the request and determines which specialized agent is best suited to handle it.
3. The selected agent processes the request using its specialized tools and knowledge.
4. The agent's response is returned to the user.

## Getting Started

### Prerequisites

- Python 3.9+
- Required packages (install via `pip install -r requirements.txt`)

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env to add your API keys
```

### Running the Example

To see the system in action, run the example script:

```bash
python src/example.py
```

This will demonstrate how the Supervisor routes different types of requests to the appropriate specialized agents.

## Customization

### Adding New Agents

To add a new specialized agent:

1. Create a new directory in `src/agents/` for your agent.
2. Implement the agent by extending the `BaseReActAgent` class.
3. Define the agent's tools and prompts.
4. Update the Supervisor to include your new agent.

### Modifying Existing Agents

Each agent has its own set of tools and prompts that can be customized:

- **Tools**: Located in `src/agents/<agent_name>/tools.py`
- **Prompts**: Located in `src/agents/<agent_name>/prompts.py`

## Architecture Details

### Supervisor

The Supervisor is responsible for:
- Analyzing user requests
- Routing requests to the appropriate agent
- Managing the overall workflow
- Synthesizing results from multiple agents if necessary

### Base Agent

The Base Agent provides:
- Common state management
- Graph construction
- Model calling infrastructure
- Tool execution

### Specialized Agents

Each specialized agent extends the Base Agent and adds:
- Domain-specific tools
- Specialized prompts
- Custom response formatting

## License

[MIT License](LICENSE)