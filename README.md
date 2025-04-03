# PullHero Python Client

PullHero is an agentic coding assistant designed to enhance your workflow by automating code reviews, consultations, documentation improvements, and more. This client allows you to integrate PullHero's capabilities into your Python projects seamlessly.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [CLI Commands](#cli-commands)
  - [Environment Variables](#environment-variables)
  - [GitHub Actions Workflows](#github-actions-workflows)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Introduction

PullHero is a powerful tool designed to assist developers by automating various aspects of code review, code improvement, and documentation. It utilizes advanced language models to provide intelligent suggestions and reviews, helping to maintain high code quality and efficiency.

## Features

- **Code Review**: Automatically review pull requests and provide detailed feedback.
- **Code Improvement**: Suggest and apply code improvements based on repository context.
- **Consultation**: Provide insights and recommendations based on project context.
- **Documentation**: Generate and improve project documentation.
- **Automated Workflows**: Integrate with GitHub Actions for seamless CI/CD pipeline integration.

## Installation

To install the PullHero Python client, you can use `pip`:

```sh
pip install pullhero
```

## Usage

### CLI Commands

PullHero provides a command-line interface (CLI) for easy interaction. Here are some of the available commands:

- **Display Banner**:
  ```sh
  pullhero --banner
  ```

- **Display Version**:
  ```sh
  pullhero --version
  ```

- **Run Code Action**:
  ```sh
  pullhero --vcs-provider <provider> --vcs-token <token> --vcs-repository <repo> --vcs-change-id <id> --vcs-change-type <type> --vcs-base-branch <base> --vcs-head-branch <head> --agent code --agent-action <action> --llm-api-key <key> --llm-api-host <host> --llm-api-model <model>
  ```

- **Run Review Action**:
  ```sh
  pullhero --vcs-provider <provider> --vcs-token <token> --vcs-repository <repo> --vcs-change-id <id> --vcs-change-type <type> --vcs-base-branch <base> --vcs-head-branch <head> --agent review --agent-action <action> --llm-api-key <key> --llm-api-host <host> --llm-api-model <model>
  ```

- **Run Consult Action**:
  ```sh
  pullhero --vcs-provider <provider> --vcs-token <token> --vcs-repository <repo> --vcs-change-id <id> --vcs-change-type <type> --vcs-base-branch <base> --vcs-head-branch <head> --agent consult --agent-action <action> --llm-api-key <key> --llm-api-host <host> --llm-api-model <model>
  ```

- **Run Document Action**:
  ```sh
  pullhero --vcs-provider <provider> --vcs-token <token> --vcs-repository <repo> --vcs-change-id <id> --vcs-change-type <type> --vcs-base-branch <base> --vcs-head-branch <head> --agent document --agent-action <action> --llm-api-key <key> --llm-api-host <host> --llm-api-model <model>
  ```

### Environment Variables

PullHero relies on several environment variables for configuration:

- `VCS_PROVIDER`: The version control system provider (e.g., `github`, `gitlab`).
- `VCS_TOKEN`: The