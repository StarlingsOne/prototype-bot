# prototype-bot
Prototyping small SocialPredict bot

# NO PUSH TO MAIN WITHOUT PULL REQUEST! ONLY YOU CAN PREVENT FOREST FIRES!

# llmconviction

# Conformal Learning Bot Based Upon LLM Output

Test out a bot designed to use LLM's to classify sentiment and conviction level so that we can experiment with conformal prediction.

## QuickStart

### Quickstart - Testing Out an LLM Value and Conviction Object Generation

* This quickstart assumes a reasonably updated MacOS or Linux Machine with`docker` as well as `docker compose` installed. Ensure you are using `docker compose` and not the deprecated `docker-compose`.

1. On your local machine, create a directory to store keys in your $HOME directory `~`.

```
mkdir playground_keys/
```

2. Within that, make another directory, `gemini/`
3. Note, this directory will NOT go in the repo EVER. This is designed to be in a location parallel to the repo in a conventional location.
4. Add a file `gemini_key` and put your Gemini API key in here. Again DO NOT REMOVE `keys/` from the `.gitignore` file for risk of leaking this online.

5. Navigate to the root directory in your terminal and do: `./run start` ... which will start up a containerized service.
6. Your terminal will put you within the containerized service at `root@container:/app#`. From here you can see that you have access to directories `app/` and `keys/` as well as `requirements.txt`.
7. Do `exit`, which will allow you to exit from the container. You can get back into the container with `./run bash`.
8. Having confirmed that, you can run a few different python scripts.

* `./app/input/test [QUERY]` will generate a response from an input query, presuming you are in the `/app` directory.

#### Osnat, fix the rest of the commands later

* `./app/readnews --output [FILE] [TOPIC]` will read news about "TOPIC" to the file "OUTPUT" with the default being `news_result.csv`
* `./app/sentiment --topic [TOPIC] --file [FILE] --output [OUTPUT]` gives a `json` formatted output sentiment and conviction level on a particular topic found in a particular file, based upon `gemini-1.5-flash`.
* For example: `./app/sentiment --topic "nvidia" --file "exported_news.csv" --output "sentiment_result_20250202"`

### to do: figure out ways for bot to connect to SocialPredict API endpoints and place bets

