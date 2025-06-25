import asyncio
from dolphin_mcp import run_interaction, reasoning

def print_trace(content):
 print(content)

async def main():
    result = await run_interaction(
        user_query="""
create the PRD for task API feature for me 
in the repo EkoCommunications/EkoNode

The requirement is to have CRUD API for task feature
""",

        guidelines="""
Your job is to create a Product Requirement Document (PRD) at PRD.md based on the feature the user has requested based on the following guidelines:
0. Assign a <feature_id> string which is based on current timestamp and should be in <XXX-YYMMDDHHmm> format where XXX can be any capital letter alphabet A-Z that you may derive from the feature briefing - for example feature_id = ACV-2506170933
1. Figure out the correct repository the user is looking to do grooming on, or ask the user if you are not sure. Here's the list of typical repository:
-- convolabai/ekoai-task, main branch: staging
-- convolabai/megabot
-- convolabai/convolab-livechat
-- convolabai/ekoai-assistant
-- touchaponk/langhook
-- convolabai/amity-dolphin-mcp
-- amityco/robotics-android, main branch: develop
-- EkoCommunications/EkoCore
-- EkoCommunications/EkoNode
-- convolabai/ekoai-console

2. Create issue into that repository with the following message:
Topic: "Create PRD for feature {feature_id}"
Content: '''
Create Product Requirement Document (PRD) markdown file for the following feature: {feature description}

Guidelines: Read .docs/PRODUCT.md  to get context of the system, and .docs/PRD_TEMPLATE.md to study template of the PRD to create. Your PRD MUST BE on .docs/{feature_id}/PRD.md. Do NOT add other section about technical detail into your PRD - this will be appended in later steps.
'''
3. [IMPORTANT] Once the issue is created, assign the issue to copilot

4. Once completed, return the issue # and link to the issue to the user AND add in '<monitor source = "github" callback_content = "PRD approved">Monitor when Github Pull Request ID with feature id {feature_id} is approved. You should look for github.pull_request.*.updated event</monitor>' where {feature_id} is ID of the feature you've just created
""",
        model_name="o4-mini",  # Optional, will use default from config if not specified
        mcp_server_config_path="./mcp_config.json",
        quiet_mode=False,  # Optional, defaults to False
        use_reasoning=True,
        reasoning_config=reasoning.ReasoningConfig(max_iterations=40, reasoning_trace=print_trace, enable_code_execution=True),
    )
    print(result)

# Run the async function
asyncio.run(main())