# PullHero 🤖⚡

[![GitHub Release](https://img.shields.io/github/v/release/ccamacho/pullhero?include_prereleases&style=flat-square)](https://github.com/ccamacho/pullhero/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-PullHero-blue.svg?logo=github&style=flat-square)](https://github.com/marketplace/actions/pullhero-ai-code-review)

**AI-Powered Code Guardian**  
Automated code reviews with intelligent feedback and approval recommendations using state-of-the-art language models.




![PullHero in Action](https://user-images.githubusercontent.com/3284836/268842123-abc4d3e4-5b9a-4d8e-9f1a-2e3a7c8d3b7a.png)  
*(Example comment from PullHero in a PR)*

## Features ✨

- 🧠 **Smart Code Analysis** - Deep context-aware reviews using DeepSeek or OpenAI
- 📚 **Repository Understanding** - Code digest generation via [GitIngest](https://github.com/cyclotruc/gitingest)
- ✅ **Clear Voting System** - +1 (Approve) or -1 (Request Changes) recommendations
- 🔌 **Multi-LLM Support** - Compatible with DeepSeek and OpenAI APIs
- 📝 **Detailed Feedback** - Actionable suggestions in PR comments
- 🔒 **Secure Configuration** - Encrypted secret handling through GitHub
- ⚡ **Fast Execution** - Optimized Python implementation

## Quick Start 🚀

### 1. Basic Setup

Add the following to your `.github/workflows/pullhero.yml`:

```yaml
name: PullHero Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Analyze with PullHero
        uses: ccamacho/pullhero@v1
        with:
          api-key: ${{ secrets.LLM_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Configure Secrets

To securely configure PullHero, follow these steps:

1. Go to your repository on GitHub.
2. Navigate to **Settings → Secrets and variables → Actions**.
3. Click **New repository secret**.
4. Add the following secrets:
   - **LLM_API_KEY**: Your DeepSeek or OpenAI API key.
   - **GITHUB_TOKEN**: This is automatically provided by GitHub (no action needed).

### 3. Configuration Options

#### Input Parameters

| Parameter       | Required | Default     | Description                               |
|----------------|----------|-------------|-------------------------------------------|
| `api-key`       | Yes      | -           | API key for LLM provider                  |
| `github-token`  | Yes      | -           | GitHub access token                       |
| `provider`      | No       | `openai`    | Either `deepseek` or `openai`             |
| `model`         | No       | `gpt-4-turbo` | Model name (e.g., `deepseek-chat-1.3`)    |
| `digest-length` | No       | `4096`      | Maximum characters for code digest        |
| `temperature`   | No       | `0.2`       | LLM creativity (0-2)                      |
| `max-feedback`  | No       | `1000`      | Maximum characters in feedback            |

### Full Configuration Example

```yaml
uses: ccamacho/pullhero@v1
with:
  api-key: ${{ secrets.DEEPSEEK_KEY }}
  github-token: ${{ secrets.GITHUB_TOKEN }}
  provider: deepseek
  model: deepseek-coder-1.3-instruct
  digest-length: 8192
  temperature: 0.3
  max-feedback: 1500
```

## Security & Permissions 🔐

### Required Permissions

Ensure your workflow has the following permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

### Security Best Practices

- **Use Least-Privilege API Keys:** Restrict API keys to only necessary permissions.
- **Rotate Keys Regularly:** Update API keys periodically.
- **Monitor Usage:** Check usage logs on your LLM provider's dashboard.
- **Restrict Workflow Triggers:** Limit when the action runs:

```yaml
on:
  pull_request:
    paths:
      - 'src/**'
      - 'lib/**'
```

## Troubleshooting 🐞

### Common Issues

| Symptom             | Solution                                |
|---------------------|-----------------------------------------|
| Missing API key     | Verify secret name matches workflow input |
| Model not found     | Check provider/model compatibility      |
| Long processing     | Reduce `digest-length` value            |
| Truncated feedback  | Increase `max-feedback` value           |
| Generic responses   | Adjust `temperature` (0.1-0.5 recommended)|

### Debugging

Add a debug step to your workflow:

```yaml
- name: Debug
  run: echo "Digest: $(cat digest.txt)"
```

## Development Contributions 👩‍💻

### Local Setup

- **Clone the repository:**

  ```bash
  git clone https://github.com/ccamacho/pullhero.git
  cd pullhero
  ```

- **Set up a Python virtual environment:**

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-dev.txt
  ```

### Release Process

Bump the version in `action.yml` and create a tagged release:

```bash
git tag -a v1.2.3 -m "Release notes"
git push origin --tags
```

## FAQ ❓

- **Q: How much does it cost?**  
  **A:** Costs depend on the LLM provider. Typical cost is 0.10–0.50 per PR.

- **Q: Can I use GPT-3.5?**

  ```yaml
  with:
    model: gpt-3.5-turbo
  ```

- **Q: Privacy of code?**  
  **A:** Code digest stays within GitHub infrastructure. API calls contain only diffs and digest.

## License & Credits 📛

**License:** Apache 2 (Full text in `LICENSE`)

**Credits:**

- Built with [GitIngest](https://github.com/cyclotruc/gitingest)
- Inspired by Docling
- LLM integrations via OpenAI/DeepSeek APIs

🎡 **Maintained by [ccamacho](https://github.com/ccamacho)**  
💬 Create an Issue for support
