#!/usr/bin/env python3
"""
Demonstration of the multi-step reasoning functionality.

This script shows how to use the new reasoning capabilities with
both simple and complex examples.
"""
import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import modules directly to avoid dependency issues
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "dolphin_mcp"))
from reasoning import ReasoningConfig
# Note: Actual run_interaction requires full dependencies


async def demo_simple_reasoning():
    """Demonstrate simple reasoning without actual MCP servers."""
    print("=== Simple Reasoning Demo ===")
    print("This would normally require MCP servers, so we'll just show the configuration")
    
    # Create reasoning configuration
    reasoning_config = ReasoningConfig(
        max_iterations=5,
        enable_planning=True,
        enable_code_execution=True
    )
    
    print(f"Reasoning Config:")
    print(f"  Max iterations: {reasoning_config.max_iterations}")
    print(f"  Planning enabled: {reasoning_config.enable_planning}")
    print(f"  Code execution enabled: {reasoning_config.enable_code_execution}")
    
    # Example of how you would use it with actual servers
    print("\nExample usage (requires actual MCP servers):")
    print("""
    result = await run_interaction(
        user_query="Calculate the fibonacci sequence up to 10 numbers",
        reasoning_config=reasoning_config,
        use_reasoning=True,
        guidelines="Show your work step by step"
    )
    """)


async def demo_reasoning_prompts():
    """Demonstrate the reasoning system prompts."""
    print("\n=== Reasoning Prompts Demo ===")
    
    from reasoning import (
        get_reasoning_system_prompt,
        get_feedback_system_prompt,
        get_user_prompt_initial
    )
    
    # Show the reasoning system prompt
    reasoning_prompt = get_reasoning_system_prompt()
    print("Reasoning System Prompt (first 500 chars):")
    print(reasoning_prompt[:500] + "...")
    
    # Show feedback/planning prompt
    feedback_prompt = get_feedback_system_prompt(
        "What is the most efficient sorting algorithm?",
        "Provide Big O notation and examples"
    )
    print(f"\nFeedback Prompt Length: {len(feedback_prompt)} characters")
    
    # Show initial user prompt
    user_prompt = get_user_prompt_initial(
        "Calculate fibonacci numbers",
        "Show step by step",
        "Plan: First understand the problem, then implement iteratively"
    )
    print(f"\nUser Prompt Length: {len(user_prompt)} characters")


async def demo_code_execution():
    """Demonstrate the Python code execution capability."""
    print("\n=== Code Execution Demo ===")
    
    from reasoning import python_interpreter, extract_code_blocks
    
    # Test Python execution with persistent context
    context = {}
    
    # Step 1: Initialize variables
    code1 = """
# Calculate fibonacci sequence
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Store some initial values
fib_numbers = []
for i in range(10):
    fib_numbers.append(fibonacci(i))

print(f"First 10 fibonacci numbers: {fib_numbers}")
"""
    
    print("Executing Step 1:")
    output1 = python_interpreter(code1, context)
    print(output1)
    
    # Step 2: Use variables from previous execution
    code2 = """
# Analyze the fibonacci sequence
total = sum(fib_numbers)
average = total / len(fib_numbers)

print(f"Sum of fibonacci numbers: {total}")
print(f"Average: {average:.2f}")

# Check for even numbers
even_fibs = [x for x in fib_numbers if x % 2 == 0]
print(f"Even fibonacci numbers: {even_fibs}")
"""
    
    print("\nExecuting Step 2 (using variables from Step 1):")
    output2 = python_interpreter(code2, context)
    print(output2)
    
    # Test code extraction
    text_with_code = """
    Here's some analysis code:
    ```python
result = max(fib_numbers)
print(f"Largest fibonacci number: {result}")
    ```
    """
    
    extracted_code = extract_code_blocks(text_with_code)
    print(f"\nExtracted code blocks: {extracted_code}")
    
    if extracted_code:
        print("Executing extracted code:")
        output3 = python_interpreter(extracted_code[0], context)
        print(output3)


async def demo_pattern_detection():
    """Demonstrate pattern detection for final answers."""
    print("\n=== Pattern Detection Demo ===")
    
    from reasoning import extract_final_answer
    
    # Example text with final answer
    text_with_answer = """
    After careful analysis of the fibonacci sequence, I can conclude:
    
    The fibonacci sequence demonstrates exponential growth, with each number
    being the sum of the two preceding ones.
    
    ```final_answer
    The fibonacci sequence up to 10 numbers is: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    The sum is 88 and the average is 8.8
    ```
    """
    
    answer = extract_final_answer(text_with_answer)
    print(f"Detected final answer: {answer}")
    
    # Example without final answer
    text_without_answer = "Still thinking about the problem..."
    answer2 = extract_final_answer(text_without_answer)
    print(f"No final answer detected: {answer2}")


async def main():
    """Run all demonstrations."""
    print("🤖 Dolphin MCP Multi-Step Reasoning Demo")
    print("=" * 50)
    
    await demo_simple_reasoning()
    await demo_reasoning_prompts()
    await demo_code_execution()
    await demo_pattern_detection()
    
    print("\n" + "=" * 50)
    print("Demo completed! The reasoning system is ready to use.")
    print("\nTo use with actual MCP servers, ensure you have:")
    print("1. Valid config.yml with model configurations")
    print("2. MCP servers configured in mcp_config.json")
    print("3. Call run_interaction() with reasoning_config and use_reasoning=True")


if __name__ == "__main__":
    asyncio.run(main())