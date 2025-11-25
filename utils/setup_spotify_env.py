import os

def setup():
    print("--- Spotify Environment Setup ---")
    print("This script will help you create or update your .env file with Spotify credentials.")
    
    client_id = input("Enter your Spotify Client ID: ").strip()
    client_secret = input("Enter your Spotify Client Secret: ").strip()
    redirect_uri = input("Enter Redirect URI (default: http://localhost:5000/spotify/callback): ").strip()
    
    if not redirect_uri:
        redirect_uri = "http://localhost:5000/spotify/callback"
        
    content = f"SPOTIFY_CLIENT_ID={client_id}\n"
    content += f"SPOTIFY_CLIENT_SECRET={client_secret}\n"
    content += f"SPOTIFY_REDIRECT_URI={redirect_uri}\n"
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("\n✅ .env file updated successfully!")
    print("You can now restart your application.")

if __name__ == "__main__":
    setup()

