# 🏠 RE Engine - Mallorca Real Estate Analyzer

A Streamlit web application that analyzes Mallorca real estate properties using AI to provide comprehensive investment insights and automatically writes results to Google Sheets.

## Features

- 🔍 **Property Data Extraction**: Fetches detailed property information from Idealista API
- 🤖 **AI Analysis**: Uses OpenAI to provide critical investment analysis and risk assessment
- 📊 **Google Sheets Integration**: Automatically writes results to your specified Google Sheet
- 💰 **Reform Cost Calculation**: Intelligent cost estimation based on property condition and type
- 🎯 **Investment Priority Scoring**: A/B/C ranking system for investment potential
- 📧 **Professional Email Templates**: Generates email drafts for agent inquiries

## Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd re-engine
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   IDEALISTA_API_KEY=your_idealista_rapidapi_key_here
   ```

4. **Set up Google Sheets authentication**
   - Create a Google service account with Sheets API access
   - Download the JSON key file and save as `service_account.json`
   - Share your target Google Sheet with the service account email

5. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

## Deployment to Streamlit Cloud

### Step 1: Prepare Your Repository

Make sure your repository contains:
- `streamlit_app.py` (main app file)
- `re_engine_core.py` (core processing logic)
- `requirements.txt` (dependencies)
- `reform_cost.csv` (reform cost reference data)

### Step 2: Set Up Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create a Service Account:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Give it a name (e.g., "re-engine-sheets")
   - Grant "Editor" role
   - Create and download JSON key

### Step 3: Share Google Sheet

1. Open your target Google Sheet: "Raphael Project Selection 2025"
2. Make sure it has a tab called "Business Cases 2025"
3. Share the sheet with your service account email (found in the JSON file)
4. Give "Editor" permissions

### Step 4: Deploy to Streamlit Cloud

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial Streamlit deployment"
   git push
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io/)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `streamlit_app.py`
   - Click "Deploy"

3. **Configure Secrets**
   In Streamlit Cloud dashboard:
   - Go to your app settings
   - Click "Secrets"
   - Paste your service account JSON as `gcreds`:

   ```toml
   [gcreds]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "your-private-key-id"
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "your-service-account@your-project.iam.gserviceaccount.com"
   client_id = "your-client-id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
   
   OPENAI_API_KEY = "your_openai_api_key_here"
   IDEALISTA_API_KEY = "your_idealista_rapidapi_key_here"
   ```

### Step 5: Test Your Deployment

1. Visit your Streamlit app URL
2. Paste an Idealista property URL
3. Click "Analyze Property"
4. Check that results appear in your Google Sheet

## How It Works

1. **URL Input**: User pastes an Idealista property URL
2. **Data Extraction**: System extracts property code and fetches data via Idealista API
3. **Data Processing**: Extracts key property features (price, size, location, etc.)
4. **AI Analysis**: OpenAI analyzes the property and provides:
   - Investment priority ranking (A/B/C)
   - Reform costs per m²
   - Market comparables
   - Location scoring
   - Business case analysis
   - Professional email draft
5. **Google Sheets Output**: Results are written to the specified sheet

## Output Columns (A-W)

The system fills 23 columns with comprehensive property analysis:
- Location, Link, ChatGPT Business Case
- Priority, License status, Purchase price
- Property metrics (surface, plot, price/m²)
- Reform costs and sales projections
- Comparable properties
- Location scoring and analysis
- Professional email templates

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `IDEALISTA_API_KEY`: Your RapidAPI key for Idealista API
- `STREAMLIT_ENV`: Set to "production" to hide debug info

## Technology Stack

- **Frontend**: Streamlit
- **AI**: OpenAI GPT models (o3-2025-04-16, gpt-4o fallback)
- **Data Source**: Idealista RapidAPI
- **Storage**: Google Sheets API
- **Deployment**: Streamlit Cloud

## Support

For issues or questions, check the application logs in Streamlit Cloud dashboard or review the error messages displayed in the web interface. 