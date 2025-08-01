# Personal Life Coordination Agents

A multi-agent system for personal life coordination, featuring specialized AI agents that work together to manage shopping, health, nutrition, and scheduling tasks. **Now with LangChain integration!**

## 🏗️ Architecture

The system consists of four specialized agents:

- **Bucky** (Port 8002) - Shopping & Inventory Management
- **Luna** (Port 8003) - Health & Fitness Tracking  
- **Milo** (Port 8004) - Meal Planning & Nutrition
- **Nani** (Port 8005) - Scheduling & Calendar Management

All agents communicate through an API Gateway (Port 8000) and can coordinate with each other using the A2A (Agent-to-Agent) protocol.

## 🔄 Framework Options

This project now supports **two frameworks**:

### 1. **LangChain Framework** (Recommended) 🚀
- **LLM Integration**: Built-in support for OpenAI, Anthropic, and other LLMs
- **Rich Tool Ecosystem**: Leverages LangChain's extensive tool library
- **Memory & Context**: Built-in conversation memory and context management
- **Easy Development**: Rapid prototyping with LangChain's agent patterns

### 2. **Custom Framework** (Legacy)
- **Full Control**: Complete customization of agent behavior
- **Lightweight**: Minimal dependencies
- **Custom A2A Protocol**: Tailored agent-to-agent communication

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (optional)
- Node.js 16+ (for frontend development)
- OpenAI API key (for LangChain framework)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd personal-life-coordination-agents
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## 🔧 Framework Selection

### Using LangChain Framework (Recommended)

```bash
# Test LangChain integration
python scripts/test_langchain.py

# Start LangChain API Gateway
python api_gateway/langchain_gateway.py

# Start individual LangChain agents
python agents/bucky_shopping/langchain_agent.py
```

### Using Custom Framework

```bash
# Test custom framework
python scripts/test.py

# Start custom API Gateway
python api_gateway/src/main.py

# Start individual agents
python agents/bucky_shopping/src/main.py
```

## 📁 Project Structure

```
personal-life-coordination-agents/
├── agents/                    # Individual agent modules
│   ├── bucky_shopping/       # Shopping & inventory management
│   │   ├── src/             # Custom framework implementation
│   │   └── langchain_agent.py # LangChain implementation
│   ├── luna_health/          # Health & fitness tracking
│   ├── milo_nutrition/       # Meal planning & nutrition
│   └── nani_scheduler/       # Scheduling & calendar management
├── api_gateway/              # Central API gateway
│   ├── src/                 # Custom framework gateway
│   └── langchain_gateway.py # LangChain gateway
├── shared/                   # Shared utilities and protocols
│   ├── langchain_framework/ # LangChain-specific components
│   ├── mcp_framework/       # Custom MCP framework
│   ├── a2a_protocol/        # Agent-to-Agent communication
│   └── utils/               # Common utilities
├── frontend/                 # React frontend application
├── infrastructure/           # Deployment and infrastructure
├── config/                  # Configuration files
├── data/                    # Data storage
├── logs/                    # Application logs
└── tests/                   # Test suites
```

## 🤖 Agent Capabilities

### Bucky - Shopping Agent
- **Pantry Tracking**: Monitor inventory levels and expiration dates
- **Price Comparison**: Compare prices across different stores
- **Shopping Optimization**: Optimize shopping routes and timing
- **Deal Finding**: Identify discounts and special offers

### Luna - Health Agent
- **Fitness Tracking**: Monitor workouts and physical activity
- **Health Analysis**: Analyze health metrics and trends
- **Workout Planning**: Generate personalized workout plans
- **Recovery Monitoring**: Track recovery and rest periods

### Milo - Nutrition Agent
- **Recipe Engine**: Generate recipes based on available ingredients
- **Nutrition Analysis**: Analyze nutritional content of meals
- **Meal Planning**: Create balanced meal plans

### Nani - Scheduler Agent
- **Calendar Management**: Sync with various calendar services
- **Scheduling Optimization**: Optimize daily schedules
- **Timezone Handling**: Manage timezone conversions
- **Focus Time Blocking**: Schedule focused work periods

## 🔧 Configuration

### LangChain Configuration

```yaml
# config/bucky.yaml
agent:
  name: bucky
  port: 8002
  description: Shopping & Inventory Management Agent

llm:
  model: gpt-3.5-turbo
  temperature: 0.1
  max_tokens: 1000

tools:
  pantry_tracker:
    enabled: true
  price_comparator:
    enabled: true
  shopping_optimizer:
    enabled: true
```

### Custom Framework Configuration

```yaml
# config/bucky.yaml
agent:
  name: bucky
  port: 8002
  description: Shopping & Inventory Management Agent

database:
  url: sqlite:///data/bucky.db

tools:
  pantry_tracker:
    enabled: true
  price_comparator:
    enabled: true
  shopping_optimizer:
    enabled: true
  deal_finder:
    enabled: true
```

## 🌐 API Endpoints

### LangChain API Gateway (Port 8000)

- `GET /health` - System health check
- `GET /agents` - List all agents
- `POST /agents/{agent_name}/chat` - Chat directly with an agent
- `POST /workflow` - Execute coordinated workflows
- `POST /a2a/message` - Send A2A messages
- `POST /a2a/broadcast` - Broadcast to all agents
- `GET /a2a/history` - Get A2A message history

### Custom Framework API Gateway

- `GET /health` - System health check
- `GET /agents` - List all agents
- `POST /workflow` - Execute coordinated workflows
- `GET /workflows` - List workflow history

## 🔄 Agent-to-Agent Communication

### LangChain A2A Protocol

```python
from shared.langchain_framework.a2a_coordinator import A2AMessage, a2a_coordinator

# Send message from Bucky to Milo
message = A2AMessage(
    from_agent="bucky",
    to_agent="milo",
    intent="generate_shopping_list",
    payload={"ingredients": ["chicken", "rice", "vegetables"]},
    session_id="session_123"
)

response = await a2a_coordinator.send_message(message)
```

### Custom A2A Protocol

```python
from shared.a2a_protocol.message_router import A2AMessage

# Send message from Bucky to Milo
message = A2AMessage(
    from_agent="bucky",
    to_agent="milo",
    intent="generate_shopping_list",
    payload={"ingredients": ["chicken", "rice", "vegetables"]},
    session_id="session_123"
)
```

## 🧪 Testing

### Test LangChain Integration

```bash
# Run LangChain tests
python scripts/test_langchain.py

# Test specific components
python -m pytest tests/langchain/
```

### Test Custom Framework

```bash
# Run custom framework tests
python scripts/test.py

# Test specific components
python -m pytest tests/
```

## 📊 Monitoring

The system includes monitoring with Prometheus and Grafana:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## 🚀 Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f infrastructure/kubernetes/

# Check deployment status
kubectl get pods -n personal-life-coordination
```

## 🔄 Migration Guide

### From Custom Framework to LangChain

1. **Install LangChain dependencies**:
   ```bash
   pip install langchain langchain-openai langchain-community
   ```

2. **Update configuration**:
   ```yaml
   llm:
     model: gpt-3.5-turbo
     temperature: 0.1
   ```

3. **Use LangChain agents**:
   ```python
   from agents.bucky_shopping.langchain_agent import LangChainBuckyAgent
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `docs/` directory
- Review the agent-specific README files in each agent directory

## 🆕 What's New

### LangChain Integration (Latest)
- ✅ Full LangChain agent support
- ✅ LLM integration with OpenAI/Anthropic
- ✅ Rich tool ecosystem
- ✅ Built-in memory and context
- ✅ Enhanced A2A coordination
- ✅ Improved API Gateway
