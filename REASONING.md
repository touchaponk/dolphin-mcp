# Multi-Step Reasoning System

This document explains the new multi-step reasoning functionality added to Dolphin MCP, which implements sophisticated reasoning capabilities inspired by the provided example code.

## Overview

The multi-step reasoning system replaces the simple tool-call loop with a more sophisticated approach that includes:

1. **Planning Phase**: Generates an initial strategy for solving the problem
2. **Execution Loop**: Multi-step reasoning with code execution and tool calls
3. **Persistent Context**: Variables persist between Python code executions  
4. **Final Answer Detection**: Recognizes when the reasoning process reaches a conclusion

## Key Components

### ReasoningConfig

Configure the reasoning behavior:

```python
from dolphin_mcp.reasoning import ReasoningConfig

config = ReasoningConfig(
    max_iterations=10,          # Maximum reasoning iterations
    enable_planning=True,       # Enable initial planning phase
    enable_code_execution=True, # Enable Python code execution
    planning_model=None         # Optional: different model for planning
)
```

### Using with run_interaction

```python
from dolphin_mcp.client import run_interaction
from dolphin_mcp.reasoning import ReasoningConfig

# Configure reasoning
reasoning_config = ReasoningConfig(max_iterations=5)

# Run with reasoning enabled
result = await run_interaction(
    user_query="Calculate fibonacci numbers and analyze patterns",
    reasoning_config=reasoning_config,
    use_reasoning=True,
    guidelines="Show your work step by step with code examples"
)
```

### Using with MCPAgent

```python
from dolphin_mcp.client import MCPAgent
from dolphin_mcp.reasoning import ReasoningConfig

# Create agent with reasoning capabilities
agent = await MCPAgent.create(
    model_name="your-model",
    provider_config=config,
    reasoning_config=ReasoningConfig(enable_planning=True)
)

# Use reasoning mode
result = await agent.prompt(
    "Complex analysis question",
    use_reasoning=True,
    guidelines="Provide detailed analysis"
)

# Or use simple mode
result = await agent.prompt(
    "Simple question",
    use_reasoning=False
)
```

## Reasoning Workflow

The system follows this structured approach:

### Root Task Workflow
1. **Explore**: Understand available tools and task requirements
2. **Plan**: Draft a high-level strategy
3. **Execute**: Implement the plan with code and tool calls
4. **Conclude**: Synthesize findings into a final answer

### Step Workflow
For each step in execution:
1. **Thought**: Explain reasoning and approach
2. **Code**: Write and execute Python code
3. **Observation**: Analyze code output and continue

## Code Execution

The system can execute Python code with persistent context:

```python
# Variables persist between executions
# Step 1: Initialize
x = 10
data = [1, 2, 3, 4, 5]

# Step 2: Use previous variables  
result = x * sum(data)
print(f"Result: {result}")
```

## Final Answer Format

To indicate completion, use the final answer format:

```
```final_answer
Your final answer here
```
```

## Example Usage

See `demo_reasoning.py` for a complete demonstration of the reasoning capabilities.

## Backward Compatibility

The system maintains full backward compatibility:
- Default behavior unchanged (simple tool-call loop)
- Reasoning mode is opt-in via `use_reasoning=True`
- All existing configurations and APIs continue to work

## Configuration Options

### Global Default
Configure reasoning as the default behavior:

```python
reasoning_config = ReasoningConfig(enable_planning=True)
agent = await MCPAgent.create(reasoning_config=reasoning_config)

# Will use reasoning by default
result = await agent.prompt("Question")
```

### Per-Query Override
Override the default on a per-query basis:

```python
# Force simple mode even if reasoning is default
result = await agent.prompt("Question", use_reasoning=False)

# Force reasoning mode even if simple is default  
result = await agent.prompt("Question", use_reasoning=True, guidelines="...")
```

## Benefits

- **Better Problem Solving**: Systematic approach to complex tasks
- **Step-by-Step Analysis**: Shows working through code execution
- **Tool Integration**: Seamlessly combines reasoning with MCP tools
- **Flexible Configuration**: Choose appropriate level of reasoning
- **Transparent Process**: Clear visibility into reasoning steps