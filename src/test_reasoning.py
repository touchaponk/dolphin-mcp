"""
Test cases for the multi-step reasoning functionality.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dolphin_mcp.reasoning import (
    MultiStepReasoner, ReasoningConfig, get_reasoning_system_prompt,
    get_feedback_system_prompt, python_interpreter, extract_code_blocks,
    extract_final_answer
)


class TestReasoningPrompts:
    """Test the reasoning prompt generation functions."""
    
    def test_get_reasoning_system_prompt(self):
        """Test that the reasoning system prompt is generated correctly."""
        prompt = get_reasoning_system_prompt()
        assert "Explore" in prompt
        assert "Plan" in prompt
        assert "Execute" in prompt
        assert "Conclude" in prompt
        assert "```python" in prompt
        assert "final_answer" in prompt
    
    def test_get_feedback_system_prompt_initial(self):
        """Test initial feedback prompt generation."""
        question = "What is the best approach?"
        guidelines = "Use clear examples"
        prompt = get_feedback_system_prompt(question, guidelines, is_initial_feedback=True)
        assert "Sub-questions" in prompt
        assert "Entity Extraction" in prompt
        assert "Solution Approach" in prompt
    
    def test_get_feedback_system_prompt_followup(self):
        """Test follow-up feedback prompt generation."""
        question = "What is the best approach?"
        guidelines = "Use clear examples"
        prompt = get_feedback_system_prompt(question, guidelines, is_initial_feedback=False)
        assert "accomplished so far" in prompt
        assert "still needs to be done" in prompt


class TestCodeExecution:
    """Test the Python code execution functionality."""
    
    def test_python_interpreter_simple(self):
        """Test basic Python code execution."""
        context = {}
        code = "result = 2 + 3\nprint(result)"
        output = python_interpreter(code, context)
        assert "5" in output
        assert context["result"] == 5
    
    def test_python_interpreter_persistent_context(self):
        """Test that context persists between executions."""
        context = {}
        
        # First execution
        code1 = "x = 10"
        python_interpreter(code1, context)
        assert context["x"] == 10
        
        # Second execution using the variable from first
        code2 = "y = x * 2\nprint(y)"
        output = python_interpreter(code2, context)
        assert "20" in output
        assert context["y"] == 20
    
    def test_python_interpreter_error_handling(self):
        """Test error handling in code execution."""
        context = {}
        code = "x = 1 / 0"  # Division by zero
        output = python_interpreter(code, context)
        assert "ZeroDivisionError" in output


class TestPatternExtraction:
    """Test pattern extraction from text."""
    
    def test_extract_code_blocks(self):
        """Test extraction of Python code blocks."""
        text = """
        Here is some code:
        ```python
        print("hello")
        x = 5
        ```
        
        And another block:
        ```python
        print("world")
        ```
        """
        code_blocks = extract_code_blocks(text)
        assert len(code_blocks) == 2
        assert 'print("hello")' in code_blocks[0]
        assert 'print("world")' in code_blocks[1]
    
    def test_extract_final_answer(self):
        """Test extraction of final answer blocks."""
        text = """
        After analysis, here is my conclusion:
        ```final_answer
        The answer is 42
        ```
        """
        answer = extract_final_answer(text)
        assert answer == "The answer is 42"
        
        # Test case where no final answer exists
        text_no_answer = "Just some regular text"
        answer = extract_final_answer(text_no_answer)
        assert answer is None


class TestReasoningConfig:
    """Test the reasoning configuration."""
    
    def test_reasoning_config_defaults(self):
        """Test default configuration values."""
        config = ReasoningConfig()
        assert config.max_iterations == 10
        assert config.enable_planning is True
        assert config.enable_code_execution is True
        assert config.planning_model is None
    
    def test_reasoning_config_custom(self):
        """Test custom configuration values."""
        config = ReasoningConfig(
            max_iterations=5,
            enable_planning=False,
            enable_code_execution=False,
            planning_model="custom-model"
        )
        assert config.max_iterations == 5
        assert config.enable_planning is False
        assert config.enable_code_execution is False
        assert config.planning_model == "custom-model"


class TestMultiStepReasoner:
    """Test the multi-step reasoning engine."""
    
    def test_reasoner_initialization(self):
        """Test that the reasoner initializes correctly."""
        config = ReasoningConfig(max_iterations=5)
        reasoner = MultiStepReasoner(config)
        assert reasoner.config.max_iterations == 5
        assert isinstance(reasoner.python_context, dict)
    
    @pytest.mark.asyncio
    async def test_generate_plan_disabled(self):
        """Test plan generation when planning is disabled."""
        config = ReasoningConfig(enable_planning=False)
        reasoner = MultiStepReasoner(config)
        
        # Mock the generate function
        mock_generate = AsyncMock()
        
        plan = await reasoner.generate_plan(
            "Test question", "Test guidelines", 
            mock_generate, {}, []
        )
        
        assert "No specific plan" in plan
        mock_generate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_plan_enabled(self):
        """Test plan generation when planning is enabled."""
        config = ReasoningConfig(enable_planning=True)
        reasoner = MultiStepReasoner(config)
        
        # Mock the generate function
        mock_generate = AsyncMock(return_value={"assistant_text": "Generated plan"})
        
        plan = await reasoner.generate_plan(
            "Test question", "Test guidelines",
            mock_generate, {}, []
        )
        
        assert plan == "Generated plan"
        mock_generate.assert_called_once()


def test_integration_extract_and_execute():
    """Integration test for extracting and executing code."""
    text = """
    I need to calculate something:
    ```python
    result = 10 * 5
    print(f"Result: {result}")
    ```
    """
    
    code_blocks = extract_code_blocks(text)
    assert len(code_blocks) == 1
    
    context = {}
    output = python_interpreter(code_blocks[0], context)
    assert "Result: 50" in output
    assert context["result"] == 50


if __name__ == "__main__":
    pytest.main([__file__])