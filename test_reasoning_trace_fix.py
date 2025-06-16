#!/usr/bin/env python3
"""
Test to validate the reasoning_trace callback receives reasoning text.
"""

import sys
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import reasoning module directly to avoid client dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "dolphin_mcp"))
from reasoning import MultiStepReasoner, ReasoningConfig


class TestReasoningTraceCallback:
    """Test class for reasoning trace callback functionality."""

    @pytest.mark.asyncio
    async def test_reasoning_trace_receives_reasoning_text(self):
        """Test that reasoning_trace callback receives the reasoning text from models."""
        
        # Track what gets passed to reasoning_trace
        reasoning_trace_calls = []
        
        def mock_reasoning_trace(text):
            reasoning_trace_calls.append(text)
        
        # Create reasoning config with our mock callback
        config = ReasoningConfig(
            max_iterations=2,
            enable_planning=False,  # Skip planning for simplicity
            enable_code_execution=False,  # Skip code execution for simplicity
            reasoning_trace=mock_reasoning_trace
        )
        
        reasoner = MultiStepReasoner(config)
        
        # Mock generate_func that returns reasoning text
        call_count = 0
        async def mock_generate_func(conversation, model_cfg, all_functions, stream=False):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "assistant_text": "```final_answer\nThe answer is 42.\n```",
                    "tool_calls": [],
                    "reasoning": "Let me think step by step. The user is asking about the meaning of life. Based on Douglas Adams' work, the answer is 42."
                }
            else:
                return {
                    "assistant_text": "More thinking...",
                    "tool_calls": [],
                    "reasoning": "Additional reasoning..."
                }
        
        # Mock process_tool_call_func (not needed for this test)
        async def mock_process_tool_call_func(tc, servers, quiet_mode):
            return None
        
        # Execute reasoning loop
        success, result = await reasoner.execute_reasoning_loop(
            question="What is the meaning of life?",
            guidelines="Be concise",
            initial_plan="Answer directly",
            generate_func=mock_generate_func,
            model_cfg={"is_reasoning": True},
            all_functions=[],
            process_tool_call_func=mock_process_tool_call_func,
            servers={},
            quiet_mode=False
        )
        
        # Verify the reasoning loop succeeded
        assert success == True
        assert result == "The answer is 42."
        
        # Check what was passed to reasoning_trace
        print(f"Reasoning trace calls: {reasoning_trace_calls}")
        
        # Verify that BOTH reasoning text and assistant text are passed to reasoning_trace
        assert len(reasoning_trace_calls) >= 3  # Step info, reasoning text, and assistant_text
        
        # Find the reasoning text call
        reasoning_text_calls = [call for call in reasoning_trace_calls if "Let me think step by step" in call]
        assert len(reasoning_text_calls) == 1  # Should have the reasoning text
        assert "[REASONING]" in reasoning_text_calls[0]  # Should be prefixed with [REASONING]
        
        # Find the assistant text call
        assistant_text_calls = [call for call in reasoning_trace_calls if "final_answer" in call]
        assert len(assistant_text_calls) == 1  # Should have the assistant text
        
        print("✅ Fix confirmed: reasoning text IS passed to reasoning_trace callback")

    @pytest.mark.asyncio
    async def test_reasoning_trace_with_no_reasoning_text(self):
        """Test that reasoning_trace works normally when there's no reasoning text (backward compatibility)."""
        
        # Track what gets passed to reasoning_trace
        reasoning_trace_calls = []
        
        def mock_reasoning_trace(text):
            reasoning_trace_calls.append(text)
        
        # Create reasoning config with our mock callback
        config = ReasoningConfig(
            max_iterations=2,
            enable_planning=False,
            enable_code_execution=False,
            reasoning_trace=mock_reasoning_trace
        )
        
        reasoner = MultiStepReasoner(config)
        
        # Mock generate_func that returns NO reasoning text (normal models)
        call_count = 0
        async def mock_generate_func(conversation, model_cfg, all_functions, stream=False):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "assistant_text": "```final_answer\nThe answer is 42.\n```",
                    "tool_calls": [],
                    "reasoning": ""  # No reasoning text
                }
            else:
                return {
                    "assistant_text": "More thinking...",
                    "tool_calls": [],
                    "reasoning": ""
                }
        
        # Mock process_tool_call_func
        async def mock_process_tool_call_func(tc, servers, quiet_mode):
            return None
        
        # Execute reasoning loop
        success, result = await reasoner.execute_reasoning_loop(
            question="What is the meaning of life?",
            guidelines="Be concise",
            initial_plan="Answer directly",
            generate_func=mock_generate_func,
            model_cfg={"is_reasoning": False},
            all_functions=[],
            process_tool_call_func=mock_process_tool_call_func,
            servers={},
            quiet_mode=False
        )
        
        # Verify the reasoning loop succeeded
        assert success == True
        assert result == "The answer is 42."
        
        # Check that normal behavior still works (no reasoning text calls)
        assert len(reasoning_trace_calls) >= 2
        assistant_text_calls = [call for call in reasoning_trace_calls if "final_answer" in call]
        assert len(assistant_text_calls) == 1
        
        # Verify no reasoning text calls were made (since there was no reasoning text)
        reasoning_text_calls = [call for call in reasoning_trace_calls if "[REASONING]" in call]
        assert len(reasoning_text_calls) == 0
        
        print("✅ Backward compatibility confirmed: normal models work as before")

    @pytest.mark.asyncio
    async def test_reasoning_trace_with_empty_reasoning(self):
        """Test that reasoning_trace handles empty reasoning text correctly."""
        
        # Track what gets passed to reasoning_trace
        reasoning_trace_calls = []
        
        def mock_reasoning_trace(text):
            reasoning_trace_calls.append(text)
        
        # Create reasoning config with our mock callback
        config = ReasoningConfig(
            max_iterations=1,
            enable_planning=False,
            enable_code_execution=False,
            reasoning_trace=mock_reasoning_trace
        )
        
        reasoner = MultiStepReasoner(config)
        
        # Mock generate_func that returns empty reasoning text
        async def mock_generate_func(conversation, model_cfg, all_functions, stream=False):
            return {
                "assistant_text": "```final_answer\nDone.\n```",
                "tool_calls": [],
                "reasoning": None  # None instead of empty string
            }
        
        # Mock process_tool_call_func
        async def mock_process_tool_call_func(tc, servers, quiet_mode):
            return None
        
        # Execute reasoning loop
        success, result = await reasoner.execute_reasoning_loop(
            question="Test",
            guidelines="",
            initial_plan="",
            generate_func=mock_generate_func,
            model_cfg={},
            all_functions=[],
            process_tool_call_func=mock_process_tool_call_func,
            servers={},
            quiet_mode=False
        )
        
        # Verify no [REASONING] calls were made for None/empty reasoning
        reasoning_text_calls = [call for call in reasoning_trace_calls if "[REASONING]" in call]
        assert len(reasoning_text_calls) == 0
        
        print("✅ Edge case confirmed: None/empty reasoning text handled correctly")


if __name__ == "__main__":
    asyncio.run(TestReasoningTraceCallback().test_reasoning_trace_receives_reasoning_text())
    asyncio.run(TestReasoningTraceCallback().test_reasoning_trace_with_no_reasoning_text())
    asyncio.run(TestReasoningTraceCallback().test_reasoning_trace_with_empty_reasoning())