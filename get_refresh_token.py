"""
OAuth 2.0 Refresh Token Generator Helper Script for Blogger API v3.
Run this script once locally to generate a refresh token for headless execution (e.g. GitHub Actions).

Usage:
    python get_refresh_token.py
"""

import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/blogger"]

def main():
    print("=== Blogger API OAuth 2.0 Refresh Token Generator ===")
    client_id = input("Enter your Client ID: ").strip(" '\"\t\r\n")
    client_secret = input("Enter your Client Secret: ").strip(" '\"\t\r\n")

    if not client_id or not client_secret:
        print("Error: Client ID and Client Secret are required.")
        return

    if not client_id.endswith(".apps.googleusercontent.com"):
        print("\n[WARNING] Your Client ID does not end with '.apps.googleusercontent.com'.")
        print("Make sure you copied the full Client ID from Google Cloud Console.")


    # Prepare client configuration dictionary supporting both installed (desktop) and web apps
    # Port fixed to 8080 for easy redirect URI configuration in Google Cloud Console
    redirect_uri = "http://localhost:8080/"

    print("\nAttempting OAuth authorization on port 8080...")

    # We try 'installed' format first, and if that fails, try 'web' format
    config_types = ["installed", "web"]
    creds = None

    for config_type in config_types:
        client_config = {
            config_type: {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri, "http://localhost"]
            }
        }

        try:
            flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
            creds = flow.run_local_server(host="localhost", port=8080, prompt="consent")
            if creds:
                break
        except Exception as e:
            if config_type == config_types[-1]:
                print(f"\nAuthorization failed: {e}")
                print("\n" + "="*60)
                print("TROUBLESHOOTING 'redirect_uri_mismatch' ERROR:")
                print("1. Recommended: Go to Google Cloud Console -> Credentials.")
                print("   Create a new OAuth Client ID with Application type set to 'Desktop app'.")
                print("2. If using 'Web application', go to your Client ID settings in Google Cloud Console")
                print("   and add 'http://localhost:8080/' under Authorized redirect URIs.")
                print("="*60 + "\n")
                sys.exit(1)

    if creds:
        print("\n" + "="*50)
        print("AUTHENTICATION SUCCESSFUL!")
        print("Copying credentials into .env file...")
        print("="*50)

        # Update .env file automatically
        env_path = ".env"
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()

        keys_to_update = {
            "BLOGGER_CLIENT_ID": client_id,
            "BLOGGER_CLIENT_SECRET": client_secret,
            "BLOGGER_REFRESH_TOKEN": creds.refresh_token
        }

        new_lines = []
        updated_keys = set()
        for line in env_lines:
            key_match = False
            for k, v in keys_to_update.items():
                if line.startswith(f"{k}="):
                    new_lines.append(f"{k}={v}\n")
                    updated_keys.add(k)
                    key_match = True
                    break
            if not key_match:
                new_lines.append(line)

        for k, v in keys_to_update.items():
            if k not in updated_keys:
                new_lines.append(f"{k}={v}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        print(f"Updated {env_path} successfully!")
        print(f"BLOGGER_CLIENT_ID={client_id}")
        print(f"BLOGGER_CLIENT_SECRET={client_secret}")
        print(f"BLOGGER_REFRESH_TOKEN={creds.refresh_token}")
        print("="*50)

if __name__ == "__main__":
    main()

