### 🔩 Directory Roles

`bot_encoder/prompts/`: staging area for new prompt files (used to create bot YAMLs).

`intake_streams/prompts/prompts_repo/`: "production" destination where final, versioned prompt files are stored.

`bot_connector/`: CLI tooling for assembling YAMLs, e.g. init, update-api, market-add, etc.


### Commands

* `init` Create new config yaml using template

```
./connector init \
  --template template.yaml \
  --prompts ../bot_encoder/prompts \
  --output bots.yaml
```