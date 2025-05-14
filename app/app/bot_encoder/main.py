import argparse
import os
import google.generativeai as genai

KEY_FILE_PATH = os.path.join(os.environ["KEYS_DIR"], "gemini", "gemini_key")

try:
    with open(KEY_FILE_PATH, "r") as key_file:
        api_key = key_file.read().strip()
except FileNotFoundError:
    print(f"Error: API key file not found at {KEY_FILE_PATH}", file=sys.stderr)
    sys.exit(1)

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.0-flash")

def generate_prompt_block(vibe: str) -> str:
    prompt = (
        "Generate 10 distinctly different *middle-instruction* prompts for bots using Google Gemini Flash 2.0.\n"
        "Each prompt should help a bot decide whether the S&P 500 will go up or down between the opening price on Monday "
        "and the closing price on Friday, using the latest financial news and headlines.\n"
        f'The overall instruction for how to write these prompts is: "{vibe}".\n'
        "Separate each prompt with the delimiter: ###"
    )
    response = model.generate_content(prompt, generation_config={"temperature": 1.3})
    return response.text.strip()

def write_split_prompts_to_files(base_name: str, raw_output: str, out_dir: str = "prompts"):
    os.makedirs(out_dir, exist_ok=True)
    prompts = [p.strip() for p in raw_output.split("###") if p.strip()]

    for i, prompt in enumerate(prompts, start=1):
        filename = f"{base_name}_{i:02d}.prompt"
        filepath = os.path.join(out_dir, filename)
        with open(filepath, "w") as f:
            f.write(prompt)

    print(f"Wrote {len(prompts)} prompts to '{out_dir}'")
    return prompts

def main():
    parser = argparse.ArgumentParser(description="Generate and write Gemini bot prompts.")
    parser.add_argument("--base", required=True, help="Base bot name (e.g., 'jim')")
    parser.add_argument("--vibe", required=True, help="Creative instruction (e.g., 'risky and aggressive')")
    parser.add_argument("--output", default="prompts", help="Directory to save prompt files")
    args = parser.parse_args()

    print(f"Generating prompts with vibe: '{args.vibe}'...")
    prompt_block = generate_prompt_block(vibe=args.vibe)
    write_split_prompts_to_files(base_name=args.base, raw_output=prompt_block, out_dir=args.output)

if __name__ == "__main__":
    main()