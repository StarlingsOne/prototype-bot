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
        "Generate 10 distinctly different prompts for bots using Google Gemini Flash 2.0.\n"
        "Each prompt should help a bot decide whether the S&P 500 will go up or down between the opening price on Monday \n"
        "and the closing price on Friday, using the latest financial news and headlines.\n"
        "This is part of a weekly contest. Each bot will give a sentiment score and conviction score as a final output in json format.\n"
        "These two variables can represent whatever, but mathematically they go into a function that is used to create a bet on a prediction market.\n"
        "The function is ABS(prediction_market_price - sentiment)*conviction ... so conceptually, the \n" 
        "sentiment is what one thinks \n"
        "the S&P500 price should be at, and conviction is the strength of that belief.\n"
        "Keep in mind that Gemini Flash 2.0 knows a few key things which are important to make use of across all prompts.\n"
        "First, Gemini knows what the current day is, day of the week and so on.\n"
        "Second, Gemini knows what the S&P500 price is at a fairly accurate timestamp.\n"
        "So a prompt could say 'Compare the opening price of the S&P500 to now, and if it's higher by 1%, \n"
        "give a high sentiment and high conviction.'\n"
        "A prompt could also say, 'If the day and time is late in the week, if it's Thursday or Friday, \n" 
        "and we are either way higher or way lower than the Monday closing price of the S&P500, our sentiment and conviction should be high.\n"
        "However the prediction market rewards early predictions, so a riskier strategy would not wait until the end of the week.\n"
        "Ultimately though, you must follow the vibe instruction coming next to design how the bots will be created.\n"
        "The most important factor is the vibe instruction, which is coming from a human user. Follow that first, use the above as tools.\n"
        f'The overall vibe instruction for how to write these prompts is: "{vibe}".\n'
        "Do not include sentiment scores in THIS response, but rather prompts. You don't have to give any instructions about json.\n"
        "This will be covered elsewhere. However you can give instructions about sentiment and conviction.\n"
        "The json information above is just for context informing you how it will be used.\n"
        "Separate each prompt with the delimiter: ###"
        "Wrap each prompt in triple hashtags, like this: \n"
        "###\n"
        "[first prompt here]\n"
        "###\n"
        "###\n"
        "[second prompt here]\n"
        "###\n"
        "(…and so on for all 10 prompts)"
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