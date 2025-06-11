import asyncio
from dolphin_mcp import run_interaction, reasoning

async def main():
    result = await run_interaction(
        user_query="""
How much the bots cloud cost for may 2025?""",

        guidelines="""
Bot1 and Bot2 is just the version of bot, please focus only total.

Local Directory Files:
- ASOL Infrastructure Cost.xlsx
""",
        model_name="gpt-4.1",  # Optional, will use default from config if not specified
        mcp_server_config_path="./mcp_config.json",
        quiet_mode=False,  # Optional, defaults to False
        use_reasoning=True,
        reasoning_config=reasoning.ReasoningConfig(max_iterations=20)
    )
    print(result)

# Run the async function
asyncio.run(main())