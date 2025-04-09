# (pullhero)

This the pullhero python client.

## How to push a code review

```bash
pullhero --vcs-provider github \
         --vcs-token ghp_B...sw \
         --vcs-repository pullhero/python-client \
         --vcs-change-id 1 \
         --vcs-change-type issue_with_pr \
         --vcs-base-branch unknown \
         --vcs-head-branch unknown \
         --agent review \
         --agent-action comment \
         --llm-api-key sk-ec....e4 \
         --llm-api-host api.deepseek.com \
         --llm-api-model deepseek-chat
```

## How to push a README.md documentation improvement

```bash
pullhero --vcs-provider github \
         --vcs-token ghp_B...sw \
         --vcs-repository pullhero/python-client \
         --vcs-change-id 11111 \
         --vcs-change-type whatever \
         --vcs-base-branch main \
         --vcs-head-branch unknown \
         --agent document \
         --agent-action comment \
         --llm-api-key 3....et \
         --llm-api-host api.mistral.ai \
         --llm-api-model mistral-large-latest
```

## How to push the consult agent

```bash
pullhero --vcs-provider github \
         --vcs-token ghp_B...sw \
         --vcs-repository pullhero/python-client \
         --vcs-change-id 1111 \
         --vcs-change-type whatever \
         --vcs-base-branch whatever \
         --vcs-head-branch whatever \
         --agent consult \
         --agent-action comment \
         --llm-api-key 3....et \
         --llm-api-host api.mistral.ai \
         --llm-api-model mistral-large-latest
```

## How to run the code improvement agent

```bash
pullhero --vcs-provider github \
         --vcs-token ghp_B...sw \
         --vcs-repository pullhero/python-client \
         --vcs-change-id 4 \
         --vcs-change-type whatever \
         --vcs-base-branch "main" \
         --vcs-head-branch "feature_test" \
         --agent code \
         --agent-action comment \
         --llm-api-key 3....et \
         --llm-api-host api.mistral.ai \
         --llm-api-model mistral-large-latest
```
