"""
Quick test of reasoning functionality without full client dependencies.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import the reasoning module directly to avoid client dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "dolphin_mcp"))
from reasoning import (
    python_interpreter, extract_code_blocks, extract_final_answer,
    get_reasoning_system_prompt, get_feedback_system_prompt, ReasoningConfig
)

def test_basic_functionality():
    """Test basic functionality without async dependencies."""
    
    # Test Python interpreter
    context = {}
    code = "result = 5 + 3\nprint(f'Result: {result}')"
    output = python_interpreter(code, context)
    print(f"Python execution output: {output}")
    assert "Result: 8" in output
    assert context["result"] == 8
    
    # Test code extraction
    text = """
    Here's some code:
    ```python
    x = 10
    print(x)
    ```
    """
    code_blocks = extract_code_blocks(text)
    print(f"Extracted code blocks: {code_blocks}")
    assert len(code_blocks) == 1
    assert "x = 10" in code_blocks[0]
    
    # Test final answer extraction
    text_with_answer = """
    After analysis:
    ```final_answer
    The answer is 42
    ```
    """
    answer = extract_final_answer(text_with_answer)
    print(f"Extracted answer: {answer}")
    assert answer == "The answer is 42"
    
    # Test system prompts
    reasoning_prompt = get_reasoning_system_prompt()
    print(f"Reasoning prompt length: {len(reasoning_prompt)}")
    assert "Explore" in reasoning_prompt
    assert "Execute" in reasoning_prompt
    
    feedback_prompt = get_feedback_system_prompt("test question", "test guidelines")
    print(f"Feedback prompt length: {len(feedback_prompt)}")
    assert "Sub-questions" in feedback_prompt
    
    # Test configuration
    config = ReasoningConfig(max_iterations=5, enable_planning=True)
    print(f"Config: max_iterations={config.max_iterations}, planning={config.enable_planning}")
    assert config.max_iterations == 5
    assert config.enable_planning is True
    
    print("All basic tests passed!")

if __name__ == "__main__":
    test_basic_functionality()