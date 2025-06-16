"""
Multi-step reasoning and planning system for Dolphin MCP.

This module implements a sophisticated reasoning approach based on the example
code provided, including planning phases and code execution loops.
"""
import re
import io
import sys
import traceback
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, AsyncGenerator, Union

logger = logging.getLogger("dolphin_mcp.reasoning")


def get_reasoning_system_prompt() -> str:
    """
    Get the system prompt for the reasoning LLM that guides multi-step execution.
    
    Based on the amity_reasoning_llm_system_prompt from the example code.
    """
    return """
You are an advanced reasoning agent that follows a structured approach to solve complex tasks using available tools.

For each task you try to solve you will follow a hierarchy of workflows: a root-level task workflow and a leaf-level step workflow.
There is one root-level workflow per task which will be composed of multiple leafs self-contained step workflows.

When solving a task you must follow this root-level workflow: 'Explore' → 'Plan' → 'Execute' → 'Conclude'.
Root Task Workflow:
    1.  Explore: Perform exploration of available tools and understand the task requirements.
    2.  Plan: Draft a high-level plan based on the results of the 'Explore' step.
    3.  Execute: Execute and operational such plan you have drafted. If while executing such plan, it turns out to be unsuccessful start over from the 'Explore' step.
    4.  Conclude: Based on the output of your executed plan, distil all findings into an answer for the proposed task to solve.

In order to advance through the Root Task Workflow you will need to perform a series of steps, for each step you take you must follow this workflow: 'Thought:' → 'Code/Call-Tool:' → 'Observation:'.
Step Workflow:
 1. Thought: Explain your reasoning and the approach you'll use.
 2. Code/Call-Tool: Write Python code or call-tool
For python code please write with the following format:
Code:
```python
your_python_code
```<end_code>
Always add the `<end_code>` tag at the end of your code block to indicate the end of the code.
Use print() in your_python_code to retain important outputs.
The code style should be step by step like a data analyst execute cell by cell in a jupyter notebook.
The context of variable context will persist between multiple executions.
You can only import library with the authorized library as follows: 
- ["numpy", "pandas", "json", "csv", "glob", "markdown", "os"]
The user will execute the code then show you the output of your code, and you will then use that output to continue your reasoning.

For Call-Tools, please follow the format and schema in Available Tools section.
**Choose only one of Code or Call-Tool in each step.**

 3. Observation: Observe the output of your code from block ```output ... ```:
When you already complete the task, Response with block ```final_answer ... ``` format as below:
```final_answer
...<Your complete explanation goes here.>...
```
When you lack sufficient information or if the user's request is ambiguous, use the format:
```final_answer
...<Your specific question for the user goes here.>...
```

Rules:
 - ALWAYS check available tools before assuming information is unavailable.
 - ALWAYS validate your assumptions with the available tools before executing.
 - IF AND ONLY IF you have exhausted all possible solution plans you can come up with and still can not find a valid answer, then provide "Not Applicable" as a final answer.
 - Use only defined variables and correct valid python statements.
 - Avoid chaining long unpredictable code snippets in one step.
 - Use python only when needed, and never re-generate the same python code if you already know is not helping you solve the task.
 - Never create any notional variables in our code, as having these in your logs will derail you from the true variables.
 - Imports and variables persist between executions.
 - Solve the task yourself, don't just provide instructions.
 """


def get_feedback_system_prompt(question: str, guidelines: str, is_initial_feedback: bool = True, all_functions: Any = None) -> str:
    """
    Get the system prompt for the feedback/planning LLM.
    
    Based on the feedback_system_prompt from the example code.
    """
    if is_initial_feedback:
        return f"""Based on the available tools and context, your job is to:
1. Understand the user query by breaking it down into smaller questions that are easier to answer.
Example:
Sub-questions:
- ...
- ...

2. Extract the entities from the user query and the guideline.
Example:
Entity Extraction:
- ...
- ...

3. Identify relevant tools and approaches that relate to the user query and guideline.
Don't include your own interpretation or explanation, just identify the relevant tools and methods.
Example:
========== START of Relevant Tools ==========
Relevant Tools and Approaches:
- Tool: tool_name - Description of how it helps
- Approach: methodology - Description of approach
========== END of Relevant Tools ==========

4. Detail any specific limitations or conditions provided in the user query and guidelines.
Example:
Constraints:
```
... the user query asks about ... which requires...
... the guideline specifies ... which means...
```

5. Outline a solution approach that addresses the constraints and leverages available tools.
Example:
Solution Approach:
- Step 1: ...
- Step 2: ...
- Step 3: ...

Available tools: \n{json.dumps([f["name"] for f in all_functions], indent=2)}\n 
"""
    else:
        return """Based on the current interaction and progress, provide feedback on:
1. What has been accomplished so far
2. What still needs to be done
3. Any adjustments to the approach
4. Next recommended steps

If the results are satisfactory, you can simply say "The reasoning and execution are correct and do not require any changes."
"""


def get_user_prompt_initial(question: str, answer_guideline: str, feedback: str) -> str:
    """
    Get the initial user prompt that combines question, guidelines, and feedback.
    
    Based on user_prompt_initial from the example code.
    """
    return f"""
Here is the question you need to answer:
- {question}

Here is the guidelines you must follow when answering the question above:
- {answer_guideline}

Here is the summary context and strategy from planning analysis:
```plan
{feedback}
```
"""


def get_user_prompt_output(output: str, feedback: str = "-") -> str:
    """
    Get the prompt for providing output feedback.
    
    Based on user_prompt_output from the example code.
    """
    return f"""
```Output
{output}
```

Feedback from the analysis:
```feedback
{feedback}
```
"""


def python_interpreter(code: str, context: Dict[str, Any]) -> str:
    """
    Execute Python code in a persistent context and return the output.
    
    Based on the python_interpreter function from the example code.
    
    Args:
        code: Python code to execute
        context: Persistent execution context (dictionary of variables)
        
    Returns:
        String output from the code execution
    """
    buf = io.StringIO()
    try:
        old_stdout = sys.stdout
        sys.stdout = buf
        exec(code, context)
        sys.stdout = old_stdout
        return buf.getvalue()
    except Exception:
        sys.stdout = old_stdout
        return traceback.format_exc()


def extract_code_blocks(text: str) -> List[str]:
    """
    Extract Python code blocks from text.
    
    Args:
        text: Text containing code blocks
        
    Returns:
        List of code strings
    """
    code_matches = re.findall(r'```python\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    # Clean up indentation and return
    cleaned_code = []
    for code in code_matches:
        # Remove common leading whitespace (dedent)
        import textwrap
        cleaned = textwrap.dedent(code).strip()
        cleaned_code.append(cleaned)
    return cleaned_code


def extract_final_answer(text: str) -> Optional[str]:
    """
    Extract final answer from text if present.
    
    Args:
        text: Text potentially containing a final answer block
        
    Returns:
        Final answer string if found, None otherwise
    """
    final_answer_matches = re.findall(r'```final_answer\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    ask_matches = re.findall(r'<ask>\s*(.*?)\s*</ask>', text, re.DOTALL | re.IGNORECASE)
    wait_matches = re.findall(r'<wait>\s*(.*?)\s*</wait>', text, re.DOTALL | re.IGNORECASE)
    if final_answer_matches:
        return final_answer_matches[-1].strip()
    elif ask_matches:
        return ask_matches[-1].strip()
    elif wait_matches:
        return wait_matches[-1].strip()
    return None


class ReasoningConfig:
    """Configuration for the reasoning system."""
    
    def __init__(self,
                 max_iterations: int = 10,
                 enable_planning: bool = True,
                 enable_code_execution: bool = True,
                 planning_model: Optional[str] = None,
                 reasoning_trace: Any = None
                 ):
        self.max_iterations = max_iterations
        self.enable_planning = enable_planning  
        self.enable_code_execution = enable_code_execution
        self.planning_model = planning_model  # If None, use same model as main reasoning
        self.reasoning_trace = reasoning_trace


class MultiStepReasoner:
    """
    Multi-step reasoning engine that implements the sophisticated reasoning approach
    from the example code.
    """
    
    def __init__(self, config: ReasoningConfig = None):
        self.config = config or ReasoningConfig()
        self.python_context: Dict[str, Any] = {}
        
    async def generate_plan(self, question: str, guidelines: str, generate_func, model_cfg: Dict, all_functions: List[Dict]) -> str:
        """
        Generate an initial plan for solving the problem.
        
        Args:
            question: The user's question
            guidelines: Answer guidelines
            generate_func: Function to generate text with the model
            model_cfg: Model configuration
            all_functions: Available functions/tools
            
        Returns:
            Generated plan as a string
        """
        if not self.config.enable_planning:
            return "No specific plan - proceeding with direct execution."

        is_reasoning = model_cfg.get("is_reasoning", False)
            
        # Create a planning conversation
        planning_conversation = [
            {
                "role": "developer" if is_reasoning else "system",
                "content": get_feedback_system_prompt(question, guidelines, is_initial_feedback=True, all_functions=all_functions)
            },
            {
                "role": "user",
                "content": f"""The User Query: 
- {question}
The Guidelines: 
- {guidelines}
"""
            }
        ]
        
        try:
            planning_result = await generate_func(planning_conversation, model_cfg, all_functions, stream=False)
            plan = planning_result.get("assistant_text", "Failed to generate plan")
            logger.info(f"Generated plan: {plan[:200]}...")
            return plan
        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}")
            return f"Planning failed: {str(e)}. Proceeding with basic approach."
    
    async def execute_reasoning_loop(self, question: str, guidelines: str, initial_plan: str,
                                   generate_func, model_cfg: Dict, all_functions: List[Dict],
                                   process_tool_call_func, servers: Dict, quiet_mode: bool) -> Tuple[bool, str]:
        """
        Execute the main reasoning loop with code execution and tool calls.
        
        Args:
            question: The user's question
            guidelines: Answer guidelines  
            initial_plan: The plan generated in the planning phase
            generate_func: Function to generate text with the model
            model_cfg: Model configuration
            all_functions: Available functions/tools
            process_tool_call_func: Function to process tool calls
            servers: MCP servers dictionary
            quiet_mode: Whether to suppress output
            
        Returns:
            Tuple of (success, final_answer_or_error)
        """

        is_reasoning = model_cfg.get("is_reasoning", False)
        # Set up the reasoning conversation
        conversation = [
            {
                "role": "developer" if is_reasoning else "system",
                "content": get_reasoning_system_prompt()
            },
            {
                "role": "user", 
                "content": get_user_prompt_initial(question, guidelines, initial_plan)
            }
        ]
        
        # Reset python context for this reasoning session
        self.python_context = {}
        
        for i in range(self.config.max_iterations):
            self.config.reasoning_trace(f"Step {i + 1}:")

            try:
                # Generate response
                result = await generate_func(conversation, model_cfg, all_functions, stream=False)
                assistant_text = result.get("assistant_text", "")
                tool_calls = result.get("tool_calls", [])
                reasoning_text = result.get("reasoning", "")

                # Pass reasoning text to reasoning_trace if available
                if reasoning_text:
                    self.config.reasoning_trace(f"[REASONING] {reasoning_text}")
                
                self.config.reasoning_trace(f"{assistant_text}")

                # Check for final answer
                final_answer = extract_final_answer(assistant_text)
                if final_answer:
                    self.config.reasoning_trace(f"Final answer detected")
                    return True, final_answer
                
                # Add assistant message to conversation
                assistant_msg = {"role": "assistant", "content": assistant_text}
                if tool_calls:
                    # Add type field to each tool call
                    for tc in tool_calls:
                        tc["type"] = "function"
                    assistant_msg["tool_calls"] = tool_calls
                conversation.append(assistant_msg)
                
                # Process tool calls if any
                tool_outputs = []
                if tool_calls:
                    for tc in tool_calls:
                        if tc.get("function", {}).get("name"):
                            result = await process_tool_call_func(tc, servers, quiet_mode)
                            if result:
                                conversation.append(result)
                                tool_outputs.append(result["content"])
                
                # Execute Python code if present
                code_blocks = extract_code_blocks(assistant_text)
                code_outputs = []
                
                if code_blocks and self.config.enable_code_execution:
                    for code in code_blocks:
                        self.config.reasoning_trace(f"Executing code: {code}\n...")
                        output = python_interpreter(code, self.python_context)
                        code_outputs.append(output)
                        self.config.reasoning_trace(f"Code Output: {output}\n...")

                # If we have code outputs, add them to the conversation
                if code_outputs:
                    combined_output = "\n".join(code_outputs)
                    conversation.append({
                        "role": "user",
                        "content": f"```output\n{combined_output}\n```"
                    })
                
                # If no code and no tool calls, we might be stuck
                if not code_blocks and not tool_calls:
                    self.config.reasoning_trace(f"No code execution or tool calls detected, might be stuck")
                    # Continue anyway, the model might be thinking
                
            except Exception as e:
                self.config.reasoning_trace(f"Error in reasoning iteration {i + 1}: {str(e)}")
                return False, f"Error during reasoning: {str(e)}"
        
        # If we reach here, we've hit max iterations without a final answer
        self.config.reasoning_trace(f"Reached max iterations ({self.config.max_iterations}) without final answer")
        return False, f"Process stopped after reaching maximum iterations ({self.config.max_iterations})."