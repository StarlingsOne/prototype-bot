
import argparse
import yaml
import os
import subprocess
import shutil
from collections import Counter
import uuid

TEMPLATE_KEYS = [
    "api_key",
    "domain",
    "since_hours",
    "username",
    "topic",
    "prompt",
    "market_ids"
]


def ensure_api_key(bot_entry):
    if not bot_entry.get("api_key"):
        bot_entry["api_key"] = str(uuid.uuid4())

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def write_yaml(data, path):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)

def load_users_from_csv(csv_path):
    with open(csv_path, 'r') as f:
        lines = [line.strip().split(",") for line in f if line.strip()]
        return dict(lines)

def get_api_keys_from_docker(container, db_user, db_name):
    csv_file = "users.csv"
    subprocess.run([
        "docker", "exec", "-i", container,
        "psql", "-U", db_user, "-d", db_name,
        "-t", "-A", "-F,", "-c", "SELECT username, api_key FROM users;"
    ], stdout=open(csv_file, "w"), check=True)
    return load_users_from_csv(csv_file)

def assert_prompt_files_exist(usernames, prompt_dir):
    for username in usernames:
        if not os.path.isfile(os.path.join(prompt_dir, f"{username}.prompt")):
            raise FileNotFoundError(f"Missing prompt file: {username}.prompt")

def cmd_init(args):
    prompt_dir = args.prompts
    template = load_yaml(args.template)
    bots = {}

    prompt_files = [f for f in os.listdir(prompt_dir) if f.endswith(".prompt")]
    botnames = [f[:-7] for f in prompt_files]

    if args.validate_prompts:
        name_counts = Counter(botnames)
        duplicates = [name for name, count in name_counts.items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate bot prompt names found: {duplicates}")

    for fname in prompt_files:
        botname = fname[:-7]
        bot_entry = template.copy()
        bot_entry["username"] = botname
        bot_entry["prompt"] = fname
        bot_entry["market_ids"] = list(bot_entry.get("market_ids", [1]))  # <- Fix alias issue
        bots[botname] = bot_entry

        if args.move_prompts:
            target_dir = os.path.join(args.prompts_repo, fname)
            shutil.move(os.path.join(prompt_dir, fname), target_dir)
            print(f"📦 Moved {fname} → {target_dir}")

    # Sort alphabetically before writing
    write_yaml(dict(sorted(bots.items())), args.output)
    print(f"✅ YAML generated with {len(bots)} bots: {args.output}")


def cmd_update_api(args):
    data = load_yaml(args.input)
    users = get_api_keys_from_docker(args.container, args.db_user, args.db_name)
    prompt_dir = args.prompts
    assert_prompt_files_exist(users.keys(), prompt_dir)

    for username, apikey in users.items():
        if username not in data:
            raise KeyError(f"Username '{username}' not found in YAML.")
        data[username]["api_key"] = apikey
        data[username]["prompt"] = f"{username}.prompt"

    write_yaml(data, args.output)
    print(f"✅ API keys and prompts updated in {args.output}")

def cmd_market_add(args):
    data = load_yaml(args.input)
    for username in data:
        if args.bot and username != args.bot:
            continue
        market_ids = data[username].get("market_ids", [])
        if args.market_id in market_ids:
            print(f"Skipping {username}: market {args.market_id} already present")
            continue
        market_ids.append(args.market_id)
        data[username]["market_ids"] = sorted(set(market_ids))

    write_yaml(data, args.output)
    print(f"✅ Market ID {args.market_id} added to applicable bots")

def cmd_market_remove(args):
    data = load_yaml(args.input)
    for username in data:
        if args.bot and username != args.bot:
            continue
        market_ids = data[username].get("market_ids", [])
        if args.market_id not in market_ids:
            print(f"Skipping {username}: market {args.market_id} not found")
            continue
        market_ids.remove(args.market_id)
        data[username]["market_ids"] = market_ids

    write_yaml(data, args.output)
    print(f"✅ Market ID {args.market_id} removed from applicable bots")

def cmd_validate(args):
    data = load_yaml(args.input)
    for username, bot in data.items():
        for key in TEMPLATE_KEYS:
            if key not in bot:
                raise ValueError(f"Bot {username} missing required field: {key}")
        if len(bot["market_ids"]) != len(set(bot["market_ids"])):
            raise ValueError(f"Bot {username} has duplicate market IDs.")
    print(f"✅ {args.input} is valid.")

def main():
    parser = argparse.ArgumentParser(description="Bot YAML Config CLI")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # init
    p_init = subparsers.add_parser('init')
    p_init.add_argument('--template', required=True)
    p_init.add_argument('--output', required=True)
    p_init.add_argument('--container', default="socialpredict-postgres-container")
    p_init.add_argument('--db-user', default="user")
    p_init.add_argument('--db-name', default="socialpredict_db")
    p_init.add_argument('--prompts', required=True, help="Directory of .prompt files")
    p_init.add_argument('--prompts-repo', default="../../intake_streams/prompts/prompts_repo", help="Where to move prompt files (if --move-prompts)")
    p_init.add_argument('--move-prompts', action="store_true", help="Move prompt files to prompts_repo")
    p_init.add_argument('--validate-prompts', action="store_true", help="Fail if duplicate prompt files found")
    p_init.set_defaults(func=cmd_init)

    # update-api
    p_update = subparsers.add_parser('update-api')
    p_update.add_argument('--input', required=True)
    p_update.add_argument('--output', required=True)
    p_update.add_argument('--prompts', required=True)
    p_update.add_argument('--container', default="socialpredict-postgres-container")
    p_update.add_argument('--db-user', default="user")
    p_update.add_argument('--db-name', default="socialpredict_db")
    p_update.set_defaults(func=cmd_update_api)

    # market-add
    p_add = subparsers.add_parser('market-add')
    p_add.add_argument('--input', required=True)
    p_add.add_argument('--output', required=True)
    p_add.add_argument('--market-id', type=int, required=True)
    p_add.add_argument('--bot', help="Limit to one bot (optional)")
    p_add.set_defaults(func=cmd_market_add)

    # market-remove
    p_rm = subparsers.add_parser('market-remove')
    p_rm.add_argument('--input', required=True)
    p_rm.add_argument('--output', required=True)
    p_rm.add_argument('--market-id', type=int, required=True)
    p_rm.add_argument('--bot', help="Limit to one bot (optional)")
    p_rm.set_defaults(func=cmd_market_remove)

    # validate
    p_validate = subparsers.add_parser('validate')
    p_validate.add_argument('--input', required=True)
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
