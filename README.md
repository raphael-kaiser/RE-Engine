# New Repository

This is a new repository created for your project.

## Getting Started

Add your project description and setup instructions here.

## Contributing

Add contribution guidelines here.

## License

Add license information here.

## Security & Deployment Notes

- Never commit `client_secret.json` or `token.json` to a public repository.
- Both files are listed in `.gitignore` for your safety.
- For Railway/cloud deployment, upload these files securely via Railway's file upload or use environment variables if possible.
- If you need to re-authenticate, do so locally and redeploy the new `token.json`.

## Setup Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Place your `client_secret.json` in the project root.
3. Run the script locally once to complete OAuth and generate `token.json`.
4. Deploy both files to Railway for cloud operation. 