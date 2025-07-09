# CodeRabbit PEM Certificate Configuration

When configuring CodeRabbit self-hosted, the `GITHUB_APP_PEM_FILE` environment
variable requires special handling.

## Important: PEM Certificate Format

The `GITHUB_APP_PEM_FILE` expects a **single-line flattened PEM certificate**,
not the standard multi-line format.

### How to Flatten Your PEM Certificate

You have two options:

#### Option 1: Flatten the Certificate (Recommended for Docker)

Convert your multi-line PEM file to a single line:

```bash
tr -d '\n' < your-key.pem
```

This will output the certificate as a single line that you can copy into your
`.env` file.

Example flattened format:

```
GITHUB_APP_PEM_FILE="-----BEGIN RSA PRIVATE KEY-----MIIEow...rest of key...-----END RSA PRIVATE KEY-----"
```

#### Option 2: Mount the File (Recommended for Kubernetes/Production)

Instead of flattening, you can mount the PEM file and reference its path:

```
GITHUB_APP_PEM_FILE=/path/to/your-key.pem
```

This approach is more secure for production deployments as it keeps the key
separate from environment variables.

## Common Issues

1. **Parse Errors**: If you see parsing errors, it's likely because the PEM
   content contains newlines. Use the flattening command above.

2. **Authentication Failures**: Ensure the PEM file is from the correct GitHub
   App and has the necessary permissions.

3. **Path Not Found**: If using the file path approach, ensure the file is
   mounted correctly in your container.

## Security Best Practices

- Never commit PEM files to version control.
- Use secrets management (Kubernetes Secrets, HashiCorp Vault) in production.
- Rotate keys regularly.
- Use the file mounting approach for production deployments.
