"""
Command-line interface for Dolphin MCP.
"""

import asyncio
import sys
import logging  # Added import
from .utils import parse_arguments
from .client import run_interaction

def main():
    """
    Main entry point for the CLI.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,  # Set logging level to DEBUG
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # Log to stderr
    )
    logger = logging.getLogger("dolphin_mcp") # Get logger instance after basicConfig
    logger.debug("Logging configured at DEBUG level.")

    # Check for help flag first
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: dolphin-mcp-cli [--model <name>] [--quiet] [--config <file>] [--log-messages <file>] [--debug] 'your question'")
        print("\nOptions:")
        print("  --model <name>         Specify the model to use")
        print("  --quiet                Suppress intermediate output (except errors)")
        print("  --config <file>        Specify a custom config file (default: mcp_config.json)")
        print("  --log-messages <file>  Log all LLM interactions to a JSONL file")
        # Consider adding a --debug flag later if needed, but basicConfig sets it for now
        print("  --help, -h             Show this help message")
        sys.exit(0)

    chosen_model_name, user_query, quiet_mode, config_path, log_messages_path = parse_arguments()
    if not user_query:
        print("Usage: dolphin-mcp-cli [--model <name>] [--quiet] [--config <file>] [--log-messages <file>] 'your question'", file=sys.stderr)
        sys.exit(1)

    # We do not pass a config object; we pass config_path
    final_text = asyncio.run(run_interaction(
        user_query=user_query,
        model_name=chosen_model_name,
        config_path=config_path,
        quiet_mode=quiet_mode,
        log_messages_path=log_messages_path
    ))

    print("\n" + final_text.strip() + "\n")

if __name__ == "__main__":
    main()
