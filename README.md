```markdown
# PullHero

PullHero is a Python client designed to assist developers with code reviews, documentation improvements, and consultations using artificial intelligence. It integrates seamlessly with popular version control systems like GitHub and GitLab, offering a set of commands to enhance your development workflow.

## Features

- **Code Review**: Automate the review process for your pull requests and receive AI-generated feedback.
- **Documentation Improvement**: Enhance your project's documentation with suggestions powered by AI.
- **Consultation**: Get insights on issues or concerns raised in your project's issues.

## Installation

You can install PullHero using pip:

```bash
pip install pullhero
```

## Usage

### How to Push a Code Review

To submit a code review for a pull request, use the following command:

```bash
pullhero --vcs-provider github \
         --vcs-token your_github_token \
         --vcs-repository owner/repo \
         --vcs-change-id pull_request_id \
         --vcs-change-type pr \
         --vcs-base-branch main \
         --vcs-head-branch feature_branch \
         --agent review \
         --agent-action comment \
         --llm-api-key your_llm_api_key \
         --llm-api-host api.your_llm_host.com \
         --llm-api-model your_llm_model
```

### How to Push a README.md Documentation Improvement

To improve the README.md documentation, run the following command:

```bash
pullhero --vcs-provider github \
         --vcs-token your_github_token \
         --vcs-repository owner/repo \
         --vcs-change-id change_id \
         --vcs-change-type documentation \
         --vcs-base-branch main \
         --vcs-head-branch improvement_branch \
         --agent document \
         --agent-action comment \
         --llm-api-key your_llm_api_key \
         --llm-api-host api.your_llm_host.com \
         --llm-api-model your_llm_model
```

### How to Use the Consult Agent

To utilize the consult agent for issues, execute:

```bash
pullhero --vcs-provider github \
         --vcs-token your_github_token \
         --vcs-repository owner/repo \
         --vcs-change-id issue_number \
         --vcs-change-type issue \
         --vcs-base-branch main \
         --vcs-head-branch feature_branch \
         --agent consult \
         --agent-action comment \
         --llm-api-key your_llm_api_key \
         --llm-api-host api.your_llm_host.com \
         --llm-api-model your_llm_model
```

### How to Run the Code Improvement Agent

To run the code improvement agent, use:

```bash
pullhero --vcs-provider github \
         --vcs-token your_github_token \
         --vcs-repository owner/repo \
         --vcs-change-id change_id \
         --vcs-change-type code_improvement \
         --vcs-base-branch main \
         --vcs-head-branch feature_branch \
         --agent code \
         --agent-action comment \
         --llm-api-key your_llm_api_key \
         --llm-api-host api.your_llm_host.com \
         --llm-api-model your_llm_model
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for more details.
```