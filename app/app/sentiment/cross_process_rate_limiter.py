import os
import time

RATE_LIMIT_SECONDS = 6
LOCKFILE = "/tmp/analyze_sentiment.lock"

def rate_limited_generate(model, prompt):
    while True:
        now = time.time()
        last_time = 0

        if os.path.exists(LOCKFILE):
            with open(LOCKFILE, "r") as f:
                try:
                    last_time = float(f.read())
                except Exception:
                    last_time = 0

        if now - last_time < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - (now - last_time))
            continue

        try:
            with open(LOCKFILE, "w") as f:
                f.write(str(time.time()))
        except Exception:
            pass

        break

    return model.generate_content(prompt)
