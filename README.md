# AutoBlogger: Fully Automated AI Blogging System

AutoBlogger is an end-to-end Python automation system that discovers trending news from RSS feeds, rewrites articles into SEO-optimized HTML using Google Gemini AI, generates featured cover images using Pollinations AI, and publishes directly to Blogger.com via Blogger API v3 on a 4-hour GitHub Actions schedule.

---

## Features

- **Phase 1: Content Discovery**: Parses RSS feeds and scrapes full article body text using `feedparser` and `BeautifulSoup4`.
- **Phase 2: SEO Article Generation**: Uses Google Gemini API (`gemini-2.5-flash`) with strict prompt engineering to create engaging, click-worthy titles, structured HTML (`<p>`, `<h2>`, `<ul>`, `<b>`, `<i>`), and tags.
- **Phase 3: AI Cover Image Generation**: Generates 16:9 featured cover images using Pollinations.ai (Free, high-speed, no API key required).
- **Phase 4: Headless Blogger API v3 Publishing**: Integrates Google API Client Library with OAuth 2.0 refresh tokens for seamless publication to Blogger.com.
- **Phase 5: GitHub Actions Cron Scheduling**: Automated execution every 4 hours (`0 */4 * * *`) with state tracking (`processed_articles.json`) to prevent duplicate posts.

---

## Local Setup Instructions

### 1. Clone Repository & Install Dependencies

```bash
git clone <your-repo-url>
cd Blogger-Automation
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

---

### 2. Configuration & Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and configure your credentials:

| Variable | Description | Example |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API Key | `AIzaSy...` |
| `BLOGGER_BLOG_ID` | Your Blogger Blog ID | `1234567890987654321` |
| `BLOGGER_CLIENT_ID` | OAuth 2.0 Client ID | `xxx.apps.googleusercontent.com` |
| `BLOGGER_CLIENT_SECRET` | OAuth 2.0 Client Secret | `GOCSPX-xxx` |
| `BLOGGER_REFRESH_TOKEN` | OAuth 2.0 Refresh Token | `1//04xxx...` |
| `RSS_FEEDS` | Comma-separated RSS feed URLs | `https://news.google.com/rss` |

---

### 3. Step-by-Step Blogger OAuth 2.0 Credentials Setup

1. **Get Blog ID**:
   - Log into [Blogger.com](https://www.blogger.com).
   - Look at your browser address bar: `https://www.blogger.com/blog/posts/1234567890987654321`. The numeric ID at the end is your `BLOGGER_BLOG_ID`.

2. **Create OAuth Credentials in Google Cloud Console**:
   - Open [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project (e.g. `Blogger Automation`).
   - Enable **Blogger API v3** under **APIs & Services > Library**.
   - Go to **OAuth consent screen**: Choose **External**, fill required fields, and add your email as a test user.
   - Go to **Credentials > Create Credentials > OAuth client ID**:
     - Application type: **Desktop App**.
     - Download or copy your **Client ID** and **Client Secret**.

3. **Generate Refresh Token**:
   Run the interactive helper script on your local computer:
   ```bash
   python get_refresh_token.py
   ```
   Follow the prompt and log in with your Google account. The script will output your `BLOGGER_REFRESH_TOKEN`.

---

## Running the Pipeline

### Dry Run (Testing without publishing)
Test content discovery, Gemini generation, and image creation without posting to Blogger:
```bash
python main.py --dry-run
```

### Run Live Publication
```bash
python main.py
```

### Publish as Draft
```bash
python main.py --draft
```

---

## Deployment to GitHub Actions (Every 4 Hours)

1. Push this repository to GitHub.
2. Navigate to **Repository Settings > Secrets and variables > Actions**.
3. Click **New repository secret** and add each secret:
   - `GEMINI_API_KEY`
   - `BLOGGER_BLOG_ID`
   - `BLOGGER_CLIENT_ID`
   - `BLOGGER_CLIENT_SECRET`
   - `BLOGGER_REFRESH_TOKEN`
   - `RSS_FEEDS`
4. The workflow in `.github/workflows/autoblogger.yml` will automatically run every 4 hours, generating new blog posts and committing the updated `processed_articles.json` state.
