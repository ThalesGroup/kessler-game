# Security Policy

## Security considerations

Kessler is not a standalone compiled application and is there for susceptible to any security threats possible in
the execution of any unknown source code. As always, best practices apply of not executing code unless it is from a
trusted source. The code maintained on this repository will be maintained to be free of any such security
vulnerabilities.

## Reporting a Vulnerability

If a potential security issue is found, please immediately contact this repository's administrators with a detailed
explanation of the issue and potential consequences. The current administrator can be reached at
zachariah.phillips@us.thalesgroup.com

## Goods Practices to Follow

:warning:**You must never store credentials information into source code or config file in a GitHub repository**
- Block sensitive data being pushed to GitHub by git-secrets or its likes as a git pre-commit hook
- Audit for slipped secrets with dedicated tools
- Use environment variables for secrets in CI/CD (e.g. GitHub Secrets) and secret managers in production
