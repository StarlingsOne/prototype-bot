### 🔩 Directory Roles

* `bot_encoder/prompts/`: staging area for new prompt files (used to create bot YAMLs).

* `prompts/prompts/prompts_repo/`: "production" destination where final, versioned prompt files are stored.

* `bot_connector/`: CLI tooling for assembling YAMLs, e.g. init, update-api, market-add, etc.

### Commands

#### `init`

* `init` Create new config yaml using template

```
./connector init \
  --template template.yaml \
  --prompts ../bot_encoder/prompts \
  --output bots.yaml
```

#### `update`

* The update-api command reads a YAML config (like bots.yaml) and updates each bot's api_key and prompt based on what’s currently stored in the database. This would only be needed if the api keys were updated for some reason, and without wanting to delete the bots. This has not been tested.

### `register-db`

* Registers all of the bots from the yaml file into the SocialPredict database.

```
./connector register-db --yaml bots.yaml
```

#### `market-remove`

```
./connector market-remove --input bots.yaml --output bots_out.yaml --market-id 1
```

#### `market-add`

```
./connector market-add --input bots_out.yaml --output bots_out.yaml --market-id 5
```


### Fixing Market Usage

* `orchestrate` has been updated, `scheduler` and `bettingbot` should not need to be updated to work with new entry, `market_ids`, which acts as a list rather than a single entry.

### Fixing News Reading, Separate Process

* We need to fix the way news is read so that bots don't read headlines on every single invocation otherwise our database will explode.
* So we have changed the orchestrater to run readnews only if it hasn't been activated in the last 30 minutes.

### Fixing Prompt Concatenation

* Prompts now use a central, "core" prompt with prompt wrappers, headers and footers, that inject key information into the overall concatenated prompts.

### Ensure Database Tracks Which Bot Made Sentiment Analysis

* Sentiment analysis table now includes a field to track which bot it came from.

### Modify `config.yaml` to Test

* In theory if we just move the prompts and copy/paste our new bots yaml into the correct location we can test orchestration.

### Publication Date of News vs. Insertion Date of News

* The, "publication date," of an article is different than the, "insertion date," of an article, which is when we read and insert it into the database.
* In order to not overload our database, we only insert news into the database every half hour at minimum.
* However sentiment window for news reads on bot can be programmed to go as far back or not as needed.

### Deduplicating News

* We deduplicate news items using an exact match postgres function right after every insertion.

### Scheduling

* As of 31 May 2025, the gemini-flash-2.0 model allows a maximum of 62 bots across 6 markets for 4 times per day.
* This transltes to 375 bots given 4 requests per day on one market.
* Scheduling has been rate limited to once every 6 seconds which is above the once every 4 second limit.

### Inserting Bots Into SocialPredict Database

The following command should work:

```
./connector register-db --yaml bots.yaml
```

### Copying Prompts and Bots to Config

* Manually copy and paste from the `bot_connector/bots.yaml` to `orchestration/config.yaml`
* Manually copy and paste the prompts from `bot_encoder/prompts` to `prompts/prompts/prompts_repo`