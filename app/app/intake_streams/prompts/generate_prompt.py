import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_DIR = os.path.join(SCRIPT_DIR, "prompts_repo")

def generate_prompt(prompt_name: str, topic: str, headlines: str) -> str:
    prompt_path = os.path.join(PROMPT_DIR, prompt_name)
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r") as f:
        template = f.read()

    return template.format(topic=topic, headlines=headlines)
