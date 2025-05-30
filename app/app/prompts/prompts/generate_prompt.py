import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_DIR = os.path.join(SCRIPT_DIR, "prompts_repo")
HEADER_PATH = os.path.join(SCRIPT_DIR, "headers", "header.prompt")
FOOTER_PATH = os.path.join(SCRIPT_DIR, "footers", "footer.prompt")

def _load_section(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    return ""

def generate_prompt(prompt_name: str, topic: str, headlines: str) -> str:
    header = _load_section(HEADER_PATH)
    footer = _load_section(FOOTER_PATH)
    prompt_path = os.path.join(PROMPT_DIR, prompt_name)
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r") as f:
        template = f.read().strip()

    # Join only non-empty sections to avoid blank lines if header/footer is missing
    final_prompt = "\n\n".join([s for s in [header, template, footer] if s])
    return final_prompt.format(topic=topic, headlines=headlines)
