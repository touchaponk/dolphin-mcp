import asyncio
from dolphin_mcp import run_interaction, reasoning

def print_trace(content):
 print(content)

async def main():
    result = await run_interaction(
        user_query="""
From this file "Test Olaf.xlsx" , could you please help summarize how many groups of incidents there are, categorized by their root cause?
Also, I’d like to know how many incidents are similar or recurring.
use pivot tables and graph to summarize the findings clearly.
""",

        guidelines="""
1. Use the provided files to answer the user's query.
2. Create the new group of root cause at least 10 groups by analyzing each incident.
3. Re-categorize the incidents based on the new root cause groups.
4. Recurring incidents can be identified by checking if the similar incident happen many times in different period (weekly,monthly).
5. Summarize the findings using pivot tables.
6. Summarize the findings using graph.

Local Directory Files:
- ASOL Infrastructure Cost.xlsx
- Test Olaf.xlsx
""",
        model_name="o4-mini",  # Optional, will use default from config if not specified
        mcp_server_config_path="./mcp_config.json",
        quiet_mode=False,  # Optional, defaults to False
        use_reasoning=True,
        reasoning_config=reasoning.ReasoningConfig(max_iterations=40, reasoning_trace=print_trace),
    )
    print(result)

# Run the async function
asyncio.run(main())