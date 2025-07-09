# CodeRabbit Setup Guide for Mobius

This guide covers setting up CodeRabbit AI code reviews with the strictest
configuration for the Mobius platform.

## Overview

CodeRabbit provides AI-powered code reviews with support for:

- Automatic docstring generation
- Unit test generation (early access)
- Comprehensive code analysis
- Security scanning
- Multi-language support

## Configuration Files

### 1. `.coderabbit.yaml` - Main Configuration

The `.coderabbit.yaml` file in the root directory contains:

- **Assertive review profile** for detailed feedback
- **Request changes workflow** to block PRs until issues are resolved
- **All analysis tools enabled** (Ruff, ESLint, TypeScript, security scanners)
- **Path-specific instructions** for different file types
- **Automatic docstring and test generation** settings

### 2. `.env.coderabbit.sample` - Self-Hosted Configuration

For self-hosted deployments, copy `.env.coderabbit.sample` to `.env` and
configure:

- LLM provider (OpenAI, Azure OpenAI, AWS Bedrock, or Anthropic)
- Platform integration (GitHub, GitLab, Azure DevOps, or Bitbucket)
- License keys and API credentials
- Optional integrations (Jira, Linear, web search)

## Usage

### Cloud-Based (Recommended for Getting Started)

1. Install CodeRabbit from the GitHub Marketplace
2. The `.coderabbit.yaml` configuration will be automatically used
3. CodeRabbit will review all PRs with strict settings

### Self-Hosted Deployment

1. Copy `.env.coderabbit.sample` to `.env`
2. Fill in your configuration values
3. Run the Docker container:
   ```bash
   docker run --env-file .env --publish 127.0.0.1:8080:8080 \
     us-docker.pkg.dev/coderabbitprod/self-hosted/coderabbit-agent:latest
   ```
4. Verify health: `curl 127.0.0.1:8080/health`

## Key Features Configured

### 1. Automatic Docstring Generation

- Trigger: Comment `@coderabbitai generate docstrings` on any PR
- Generates Google-style docstrings for Python
- Generates JSDoc comments for TypeScript/JavaScript
- Includes examples and comprehensive documentation

### 2. Automatic Test Generation (Early Access)

- Generates pytest tests for Python code
- Generates Jest/React Testing Library tests for TypeScript
- Includes edge cases and error scenarios
- Follows AAA pattern (Arrange, Act, Assert)

### 3. Strict Code Review

- **Python**: PEP 8, type hints, FastAPI best practices
- **TypeScript**: No `any` types, React hooks best practices
- **Security**: Input validation, no hardcoded secrets
- **Performance**: Optimization requirements
- **Testing**: Coverage requirements for new code

### 4. Security Features

- Sensitive path protection (`auth/`, `security/`, `config/`)
- Security scanning with Semgrep
- Secret detection with Gitleaks (if enabled)
- Input validation requirements

## Commands

### Review Commands

- `@coderabbitai review` - Trigger incremental review
- `@coderabbitai full review` - Comprehensive review
- `@coderabbitai generate docstrings` - Auto-generate documentation
- `@coderabbitai pause` - Pause reviews on a PR

### Chat Commands

- Ask questions about code changes
- Request explanations for review feedback
- Get suggestions for improvements

## Best Practices

1. **Pre-commit Hooks**: Set up pre-commit hooks to catch issues before
   CodeRabbit review
2. **Incremental Changes**: Make smaller, focused PRs for better review quality
3. **Address Feedback**: Resolve all CodeRabbit comments before merging
4. **Documentation**: Use auto-generated docstrings as a starting point, then
   enhance
5. **Testing**: Use auto-generated tests as a foundation, add specific business
   logic tests

## Troubleshooting

### Common Issues

1. **Review Not Triggering**
   - Ensure `.coderabbit.yaml` exists in the feature branch
   - Check if the repository has CodeRabbit installed
   - Verify webhook configuration for self-hosted

2. **Docstring Generation Failing**
   - Requires Pro plan
   - Ensure proper syntax in existing code
   - Check language support (18 languages supported)

3. **Self-Hosted Connection Issues**
   - Verify firewall rules allow outbound HTTPS
   - Check API key validity
   - Ensure Docker container has network access

## Additional Resources

- [CodeRabbit Documentation](https://docs.coderabbit.ai/)
- [AST-grep Rules Guide](https://docs.coderabbit.ai/guides/review-instructions)
- [Custom Report Templates](https://docs.coderabbit.ai/guides/custom-reports)

## Support

For issues specific to the Mobius configuration:

1. Check the `.coderabbit.yaml` configuration
2. Review recent commit messages for configuration changes
3. Contact the platform team for assistance

For CodeRabbit-specific issues:

- Report at: https://github.com/coderabbitai/coderabbit-docs/issues
