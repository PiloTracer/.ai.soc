# .ai.soc — Security OS

**Autonomous AI security testing framework.** Forked from [Strix](https://github.com/usestrix/strix) by OmniSecure Inc.

.ai.soc agents act like real hackers — they run your code dynamically, find vulnerabilities, and validate them through actual proof-of-concepts. Built for developers and security teams who need fast, accurate security testing.

**Key Capabilities:**

- **Full hacker toolkit** out of the box
- **Teams of agents** that collaborate and scale
- **Real validation** with PoCs, not false positives
- **Developer-first** CLI with actionable reports
- **Auto-fix & reporting** to accelerate remediation

---

## Use Cases

- **Application Security Testing** — Detect and validate critical vulnerabilities
- **Rapid Penetration Testing** — Get penetration tests done in hours, not weeks
- **Bug Bounty Automation** — Automate bug bounty research with PoCs
- **CI/CD Integration** — Block vulnerabilities before reaching production

## Quick Start

**Prerequisites:**
- Docker (running)
- An LLM API key (OpenAI, Anthropic, Google, etc.)

### Installation & First Scan

```bash
# Install
curl -sSL https://strix.ai/install | bash

# Configure
export SOC_LLM="openai/gpt-5.4"
export LLM_API_KEY="your-api-key"

# Run first assessment
soc --target ./app-directory
```

> [!NOTE]
> First run pulls the sandbox Docker image. Results saved to `strix_runs/<run-name>`.

## Usage

```bash
# Scan a local codebase
soc --target ./app-directory

# Security review of a GitHub repository
soc --target https://github.com/org/repo

# Black-box web assessment
soc --target https://your-app.com
```

### Configuration

```bash
export SOC_LLM="openai/gpt-5.4"
export LLM_API_KEY="your-api-key"

# Optional
export LLM_API_BASE="your-api-base-url"
export PERPLEXITY_API_KEY="your-api-key"
export SOC_REASONING_EFFORT="high"
```

---

## Documentation

Full documentation at **[docs.strix.ai](https://docs.strix.ai)** — including detailed guides for usage, CI/CD, skills, and advanced configuration.

---

## Acknowledgments

This project is derived from **[Strix](https://github.com/usestrix/strix)** by OmniSecure Inc., licensed under Apache 2.0. See [NOTICE](NOTICE) and [LICENSE](LICENSE) for details.

Strix builds on the incredible work of open-source projects like [LiteLLM](https://github.com/BerriAI/litellm), [Caido](https://github.com/caido/caido), [Nuclei](https://github.com/projectdiscovery/nuclei), [Playwright](https://github.com/microsoft/playwright), and [Textual](https://github.com/Textualize/textual).

---

> [!WARNING]
> Only test apps you own or have permission to test. You are responsible for using this tool ethically and legally.
