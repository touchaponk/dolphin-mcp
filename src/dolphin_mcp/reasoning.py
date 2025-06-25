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


def get_reasoning_system_prompt(all_functions: List[Dict] = None) -> str:
    """
    Get the system prompt for the reasoning LLM that guides multi-step execution.
    
    Based on the amity_reasoning_llm_system_prompt from the example code.
    """
    tool_instructions = "Please follow the format and schema in Available Tools section."
    if all_functions:
        tool_instructions = f"""Please use the following format.

<tool_code>
{{
  \"name\": \"server_name_tool_name\"
}}
</tool_code>

Available Tools are provided below in JSON format.
```json
{ [ {"name": func["name"], "description": func["description"] } for func in all_functions] }\n
```"""

    return f"""
You are an advanced reasoning agent that follows a structured approach to solve complex tasks using available tools.

For each task you try to solve you will follow a hierarchy of workflows: a root-level task workflow and a leaf-level step workflow.
There is one root-level workflow per task which will be composed of multiple leafs self-contained step workflows.

When solving a task you must follow this root-level workflow: 'Explore' → 'Plan' → 'Execute' → 'Conclude'.
Root Task Workflow:
    1.  Explore: Perform exploration of available tools and understand the task requirements.
    2.  Plan: Draft a high-level plan based on the results of the 'Explore' step.
    3.  Execute: Execute and operational such plan you have drafted. If while executing such plan, it turns out to be unsuccessful start over from the 'Explore' step.
    4.  Conclude: Based on the output of your executed plan, distil all findings into an answer for the proposed task to solve.

In order to advance through the Root Task Workflow you will need to perform a series of steps, for each step you take you must follow this workflow: 'Thought:' → 'Action:' → 'Observation:'.
Step Workflow:
 1. Thought: Explain your reasoning and the approach you'll use for the next action.
 2. Action: Based on your thought, you must choose **one and only one** of the following actions in each step:
    - To execute Python code, use the `<python>` tag.
    - To call a tool, use the `<tool_code>` tag.
    - To provide the final answer when the task is complete, use the `<final_answer>` tag.

    **Action Formats:**

    **1. Python Code:**
    <python>
    your_python_code
    </python>
    - Use `print()` in your code to retain important outputs.
    - The code style should be step by step like a data analyst execute cell by cell in a jupyter notebook.
    - The context of variables will persist between multiple executions.
    - You can only import library with the authorized library as follows: Any.
    - The user will execute the code then show you the output of your code, and you will then use that output to continue your reasoning.

    **2. Tool Call:**
    {tool_instructions}

    **3. Final Answer:**
    <final_answer>
    ...<Your complete explanation goes here.>...
    </final_answer>

 3. Observation: After you provide a `<python>` or `<tool_code>` action, you will receive an observation from the system containing the output. Use this to inform your next step. If you provide `<final_answer>`, the process ends.

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
 - Mostly of tools call is API, so make sure you utilize the Call-Tool and Code together to maximize the efficiency of execution.
 - If user didn't mentioned to allow you to ask back to the user in the guidelines, you should complete the task by yourself.
 - Choose only one action per step, either a tool call, Python code execution, or final answer.
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

Available tools: 
{ [ {"name": func["name"], "description": func["description"] } for func in all_functions] }\n

Common Tools, The most common that you can use together with the available tools.
Python Interpreter:
- name: "python_interpreter", 
- description: "Execute Python code in a persistent context"
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
Here is the user enquiry:
- {question}

Here is the guidelines:
- {answer_guideline}

Here is the summary context and plan from human expert:
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
    code_matches = re.findall(r'<python.*?>\s*(.*?)\s*</python>', text, re.DOTALL | re.IGNORECASE)
    # Clean up indentation and return
    cleaned_code = []
    for code in code_matches:
        # Remove common leading whitespace (dedent)
        import textwrap
        cleaned = textwrap.dedent(code).strip()
        cleaned_code.append(cleaned)
    return cleaned_code


def extract_tool_calls(text: str) -> List[Dict]:
    """
    Extract tool call blocks from text.

    Args:
        text: Text containing tool call blocks

    Returns:
        List of tool call dictionaries
    """
    tool_code_matches = re.findall(r'<tool_code.*?>\s*(.*?)\s*</tool_code>', text, re.DOTALL | re.IGNORECASE)
    extracted_calls = []
    for match in tool_code_matches:
        try:
            tool_call = json.loads(match)
            extracted_calls.append(tool_call)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse tool call json: {match}")
    return extracted_calls


def extract_final_answer(text: str) -> Optional[str]:
    """
    Extract final answer from text if present.
    
    Args:
        text: Text potentially containing a final answer block
        
    Returns:
        Final answer string if found, None otherwise
    """
    final_answer_matches = re.findall(r'<final_answer.*?>\s*(.*?)\s*</final_answer>', text, re.DOTALL | re.IGNORECASE)
    ask_matches = re.findall(r'<ask.*?>\s*(.*?)\s*</ask>', text, re.DOTALL | re.IGNORECASE)
    monitor_matches = re.findall(r'<monitor.*?>\s*(.*?)\s*</monitor>', text, re.DOTALL | re.IGNORECASE)
    if final_answer_matches:
        return final_answer_matches[-1].strip()
    elif ask_matches:
        return ask_matches[-1].strip()
    elif monitor_matches:
        return monitor_matches[-1].strip()
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
        
    async def _get_tool_args_from_llm(self, tool_name: str, tool_def: Dict, conversation: List[Dict], generate_func, model_cfg: Dict) -> Dict:
        """
        Asks the LLM to generate arguments for a tool call.
        """
        self.config.reasoning_trace(f"Asking LLM to generate arguments for tool: {tool_name}")

        prompt_content = f"""You have decided to call the tool `{tool_name}`.
Based on the conversation history, please provide the arguments for this tool.
Tool Description: {tool_def.get('description')}
Tool Schema:
```json
{json.dumps(tool_def.get('parameters', {}), indent=2)}
```
Please provide *only* the JSON object for the arguments, without any other text or explanation.
"""

        # Use a copy of the conversation to avoid polluting the main reasoning flow
        args_conversation = list(conversation)
        args_conversation.append({"role": "user", "content": prompt_content})

        # Call LLM
        args_result = await generate_func(args_conversation, model_cfg, [], stream=False)
        args_text = args_result.get("assistant_text", "").strip()

        self.config.reasoning_trace(f"LLM generated arguments: {args_text}")

        # Parse the arguments
        try:
            # The model might return the JSON inside a code block.
            match = re.search(r'```(json)?\s*(.*?)\s*```', args_text, re.DOTALL)
            if match:
                args_text = match.group(2)

            parsed_args = json.loads(args_text)
            if not isinstance(parsed_args, dict):
                raise json.JSONDecodeError("Not a JSON object", args_text, 0)
            return parsed_args
        except (json.JSONDecodeError, AttributeError) as e:
            self.config.reasoning_trace(f"Failed to parse arguments for {tool_name}: {e}")
            return {"error": "Failed to generate valid JSON arguments.", "raw_response": args_text}

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
            planning_result = await generate_func(planning_conversation, model_cfg, [], stream=False)
            plan = planning_result.get("assistant_text", "Failed to generate plan")
            print(f"Generated plan: {plan}...")
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
                "content": get_reasoning_system_prompt(all_functions=all_functions)
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
                result = await generate_func(conversation, model_cfg, [], stream=False)
                assistant_text = result.get("assistant_text", "")
                self.config.reasoning_trace(f"[ASSISTANT] {assistant_text}")
                
                # Add assistant message to conversation
                assistant_msg = {"role": "assistant", "content": assistant_text}
                conversation.append(assistant_msg)

                # Process tool calls if any
                tool_calls = extract_tool_calls(assistant_text)
                if tool_calls:
                    for tc_data in tool_calls:
                        self.config.reasoning_trace(f"Processing tool call: {tc_data.get('name', 'unknown')}")
                        tool_name = tc_data.get("name")
                        if not tool_name:
                            continue

                        # Find the full function definition to validate parameters
                        full_function_def = next((f for f in all_functions if f['name'] == tool_name), None)

                        if not full_function_def:
                            error_content = f"Error calling tool {tool_name}: Tool not found."
                            self.config.reasoning_trace(error_content)
                            conversation.append(
                                {"role": "user", "content": f"<tool_output>\n{error_content}\n</tool_output>"})
                            continue

                        # Generate arguments for the tool call using the LLM
                        tool_args = await self._get_tool_args_from_llm(
                            tool_name, full_function_def, conversation, generate_func, model_cfg
                        )

                        if "error" in tool_args:
                            error_content = f"Error calling tool {tool_name}: {tool_args['error']} Raw response: {tool_args['raw_response']}"
                            self.config.reasoning_trace(error_content)
                            conversation.append(
                                {"role": "user", "content": f"<tool_output>\n{error_content}\n</tool_output>"})
                            continue

                        # Validate parameters
                        schema = full_function_def.get("parameters", {})
                        required_params = schema.get("required", [])
                        missing_params = [p for p in required_params if p not in tool_args]
                        if missing_params:
                            error_content = f"Error calling tool {tool_name}: Missing required parameters after generation: {', '.join(missing_params)}"
                            self.config.reasoning_trace(error_content)
                            conversation.append(
                                {"role": "user", "content": f"<tool_output>\n{error_content}\n</tool_output>"})
                            continue

                        # Adapt to the format expected by process_tool_call_func
                        fake_tc = {"id": f"call_{tool_name.replace('.', '_')}_{i}", "function": {"name": tool_name, "arguments": json.dumps(tool_args) }}
                        result = await process_tool_call_func(fake_tc, servers, quiet_mode)
                        if result and 'content' in result:
                            self.config.reasoning_trace(f"Tool call output: {result['content']}")
                            conversation.append({"role": "user", "content": f"<tool_output>\n{result['content']}\n</tool_output>"})
                    continue

                # Execute Python code if present
                code_blocks = extract_code_blocks(assistant_text)
                code_outputs = []

                if code_blocks and self.config.enable_code_execution:
                    logger.info(f"Executing {code_blocks}")
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
                        "content": f"<code_output>\n{combined_output}\n</code_output>"
                    })
                    continue
                
                # If no code and no tool calls, we might be stuck
                if not code_blocks and not tool_calls:
                    no_code_output_msg = f"""No code execution or tool calls detected"""
                    self.config.reasoning_trace(no_code_output_msg)
                    conversation.append({"role": "user", "content": f"<no_code_output>{no_code_output_msg}</no_code_output>"})

                conversation.append({"role": "user", "content": f"""
Based on the current stage and the plan from human expert, please provide the next step or final answer.
"""})
                # Check for final answer
                final_answer = extract_final_answer(assistant_text)
                if final_answer:
                    self.config.reasoning_trace(f"Final answer detected")
                    return True, final_answer

            except Exception as e:
                self.config.reasoning_trace(f"Error in reasoning iteration {i + 1}: {str(e)}")
                return False, f"Error during reasoning: {str(e)}"
        
        # If we reach here, we've hit max iterations without a final answer
        self.config.reasoning_trace(f"Reached max iterations ({self.config.max_iterations}) without final answer")
        return False, f"Process stopped after reaching maximum iterations ({self.config.max_iterations})."
