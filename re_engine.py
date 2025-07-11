from dotenv import load_dotenv
load_dotenv(override=True)
import os
import openai
import gspread
import http.client
import json as pyjson
import pandas as pd

SHEET_NAME = 'Raphael Project Selection 2025'
TAB_NAME = 'Business Cases 2025'
SERVICE_ACCOUNT_FILE = 'service_account.json'
REFORM_COST_CSV = 'reform_cost.csv'

# The only columns to fill, in order A-W:
COLUMNS = [
    'Location',
    'Link',
    'ChatGPT Business Case',
    'Nota Simple',
    'Priority',
    'License Yes/No',
    'Project purchase price',
    'Seaview',
    'Comments',
    'Total surface (m2) Metros construidos',
    'Plot size',
    'Price m2',
    'Reform cost (m2)',
    'Aimed Sales Price without Real Estate Agent',
    'Comparable Houses on the market 1',
    'Comparable Houses on the market 2',
    'Comparable Houses on the market 3',
    'Macro location (1-10)',
    'Micro location (1-10)',
    'Sun direction',
    'View',
    'Building',
    'Email Draft'
]

IDEALISTA_API_KEY = os.getenv('IDEALISTA_API_KEY')
IDEALISTA_API_HOST = 'idealista2.p.rapidapi.com'

if not IDEALISTA_API_KEY:
    print("[FATAL] IDEALISTA_API_KEY is not set. Please add it to your .env file or export it in your shell.")
    exit(1)
if not os.getenv('OPENAI_API_KEY'):
    print("[WARNING] OPENAI_API_KEY is not set. OpenAI completions will fail.")

def load_reform_costs():
    """Load reform costs from CSV file"""
    try:
        if os.path.exists(REFORM_COST_CSV):
            reform_df = pd.read_csv(REFORM_COST_CSV)
            return reform_df.to_dict('records')
        else:
            print(f"[WARNING] {REFORM_COST_CSV} not found. Using default values.")
            return []
    except Exception as e:
        print(f"[ERROR] Could not load reform costs: {e}")
        return []

def get_gsheet_client():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    return gc

def get_worksheet(gc, sheet_name, tab_name):
    sh = gc.open(sheet_name)
    worksheet = sh.worksheet(tab_name)
    return worksheet

def extract_property_code(url):
    return url.rstrip('/').split('/')[-1]

def fetch_idealista_api(property_code):
    conn = http.client.HTTPSConnection(IDEALISTA_API_HOST)
    headers = {
        'x-rapidapi-key': IDEALISTA_API_KEY,
        'x-rapidapi-host': IDEALISTA_API_HOST
    }
    endpoint = f"/properties/detail?country=es&propertyCode={property_code}"
    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    data = res.read()
    try:
        parsed = pyjson.loads(data.decode("utf-8"))
        # DEBUG: Uncomment next line to inspect full API response
        # print("[DEBUG] Idealista raw JSON:", pyjson.dumps(parsed, indent=2))
        return parsed
    except Exception as e:
        print(f"[ERROR] Could not parse Idealista API response: {e}")
        return {}

def extract_all_idealista_fields(api_data, url):
    """Extract every possible field from Idealista API response"""
    d = {col: 'Info Missing' for col in COLUMNS}
    d['Link'] = url
    
    if not api_data:
        return d
    
    # Basic property info - format price with euro symbol
    price = api_data.get('price')
    if price:
        d['Project purchase price'] = f"€{int(price)}"
    else:
        d['Project purchase price'] = 'Info Missing'
    
    # Location - extract neighborhood/municipality for area name
    location_area = ''
    if api_data.get('neighborhood'):
        location_area = api_data['neighborhood']
    elif api_data.get('district'):
        location_area = api_data['district']
    elif api_data.get('municipality'):
        location_area = api_data['municipality']
    elif api_data.get('address'):
        # Try to extract area from address
        location_area = api_data['address']
    
    # Clean up common Mallorca location names
    location_map = {
        'calvia': 'Calvià',
        'santa ponsa': 'Santa Ponsa',
        'camp de mar': 'Camp de Mar',
        'port andratx': 'Port Andratx',
        'andratx': 'Andratx',
        'portals': 'Portals',
        'bendinat': 'Bendinat',
        'son vida': 'Son Vida',
        'palma': 'Palma',
        'soller': 'Sóller',
        'deia': 'Deià',
        'valldemossa': 'Valldemossa',
        'costa d\'en blanes': 'Costa d\'en Blanes',
        'puerto portals': 'Puerto Portals',
        'palmanova': 'Palmanova',
        'magaluf': 'Magaluf',
        'sol de mallorca': 'Sol de Mallorca',
        'portals nous': 'Portals Nous',
        'illetes': 'Illetes',
        'cas catala': 'Cas Català',
        'genova': 'Génova',
        'son Espanyolet': 'Son Espanyolet',
        'sa rapita': 'Sa Ràpita',
        'es trenc': 'Es Trenc',
        'santanyi': 'Santanyí',
        'cala d\'or': 'Cala d\'Or',
        'porto cristo': 'Porto Cristo',
        'cala millor': 'Cala Millor',
        'alcudia': 'Alcúdia',
        'pollensa': 'Pollença',
        'puerto pollensa': 'Puerto Pollença',
        'formentor': 'Formentor'
    }
    
    # Normalize and map location
    location_lower = location_area.lower()
    for key, value in location_map.items():
        if key in location_lower:
            location_area = value
            break
    
    d['Location'] = location_area if location_area else 'Info Missing'
    
    # Size fields
    size = api_data.get('size') or api_data.get('constructedArea') or api_data.get('surface')
    if size:
        d['Total surface (m2) Metros construidos'] = str(size)
    
    plot = api_data.get('plotArea') or api_data.get('plot')
    if plot:
        d['Plot size'] = str(plot)
    
    # Calculate price per m2 - format with euro
    if size and price:
        try:
            price_m2 = int(float(price) / float(size))
            d['Price m2'] = f"€{price_m2}"
        except:
            pass
    elif api_data.get('priceByArea'):
        d['Price m2'] = f"€{int(api_data['priceByArea'])}"
    
    # Description
    d['Comments'] = api_data.get('description', 'Info Missing')
    
    # Views and features
    d['Seaview'] = 'Yes' if api_data.get('hasSeaView') else 'No'
    d['View'] = 'sea' if api_data.get('hasSeaView') else ''
    
    # Building type
    property_type = api_data.get('propertyType', '')
    extended_type = api_data.get('extendedPropertyType', '')
    home_type = api_data.get('homeType', '')
    d['Building'] = extended_type or home_type or property_type or 'Info Missing'
    
    # Extract additional features for AI to use
    features = {
        'bedrooms': api_data.get('rooms', 0),
        'bathrooms': api_data.get('bathrooms', 0),
        'floor': api_data.get('floor', ''),
        'hasLift': api_data.get('hasLift', False),
        'hasTerrace': api_data.get('hasTerrace', False),
        'hasGarden': api_data.get('hasGarden', False),
        'hasPool': api_data.get('hasPool', False),
        'hasGarage': api_data.get('hasGarage', False),
        'parkingSpace': api_data.get('parkingSpace', {}),
        'condition': api_data.get('condition', ''),
        'status': api_data.get('status', ''),
        'latitude': api_data.get('latitude', ''),
        'longitude': api_data.get('longitude', ''),
        'distance': api_data.get('distance', ''),
        'detailedType': api_data.get('detailedType', {}),
        'suggestedTexts': api_data.get('suggestedTexts', {}),
        'hasPlan': api_data.get('hasPlan', False),
        'has3DTour': api_data.get('has3DTour', False),
        'hasVideo': api_data.get('hasVideo', False),
        'hasStaging': api_data.get('hasStaging', False),
        'topNewDevelopment': api_data.get('topNewDevelopment', False),
        'newDevelopment': api_data.get('newDevelopment', False),
        'parkingSpacePrice': api_data.get('parkingSpace', {}).get('price', ''),
        'ubication': api_data.get('ubication', ''),
        'municipality': api_data.get('municipality', ''),
        'district': api_data.get('district', ''),
        'neighborhood': api_data.get('neighborhood', ''),
        'operation': api_data.get('operation', ''),
        'typology': api_data.get('typology', ''),
        'subTypology': api_data.get('subTypology', ''),
        'superTopHighlight': api_data.get('superTopHighlight', False),
        'topHighlight': api_data.get('topHighlight', False),
        'highlight': api_data.get('highlight', False)
    }
    
    # Store features in comments for AI to analyze
    d['_extracted_features'] = features
    
    return d

def filter_api_data_for_ai(api_data):
    """Filter API data to remove unnecessary verbose fields before sending to AI"""
    if not api_data:
        return {}
    
    # Fields to exclude - images, videos, comments, and other verbose data
    exclude_fields = {
        'multimedia', 'images', 'videos', 'photos', 'gallery', 'picture', 'image',
        'description', 'comments', 'detailedDescription', 'longDescription',
        'suggestedTexts', 'texts', 'content', 'htmlDescription',
        'videoUrl', 'video', 'videoTour', 'virtualTour', '3dTour',
        'plan', 'floorPlan', 'blueprint', 'layout',
        'contact', 'agency', 'agent', 'phone', 'email', 'website',
        'advertisement', 'marketing', 'promotion', 'featured',
        'metadata', 'tracking', 'analytics', 'stats'
    }
    
    def clean_dict(data):
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Skip fields that contain verbose data
                if any(exclude in key.lower() for exclude in exclude_fields):
                    continue
                
                # Recursively clean nested dictionaries
                if isinstance(value, dict):
                    cleaned_value = clean_dict(value)
                    if cleaned_value:  # Only add if not empty
                        cleaned[key] = cleaned_value
                elif isinstance(value, list):
                    # Clean lists but skip if they contain media/verbose content
                    if not any(exclude in key.lower() for exclude in exclude_fields):
                        cleaned_list = []
                        for item in value:
                            if isinstance(item, dict):
                                cleaned_item = clean_dict(item)
                                if cleaned_item:
                                    cleaned_list.append(cleaned_item)
                            elif isinstance(item, str) and len(item) < 200:  # Skip very long strings
                                cleaned_list.append(item)
                            elif not isinstance(item, str):
                                cleaned_list.append(item)
                        if cleaned_list:
                            cleaned[key] = cleaned_list
                else:
                    # Keep simple values, but truncate very long strings
                    if isinstance(value, str) and len(value) > 500:
                        continue  # Skip very long text fields
                    cleaned[key] = value
            return cleaned
        return data
    
    return clean_dict(api_data)

def ai_analyze_property(api_data, extracted_data, reform_costs):
    """Use AI to analyze property and fill remaining fields"""
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Filter API data to remove verbose/unnecessary fields
    filtered_api_data = filter_api_data_for_ai(api_data)
    
    system_message = """You are a CRITICAL Mallorca real estate investment analyst. Your job is to evaluat the property objectively. Be harsh, realistic, and conservative in all estimates.

STRICT REQUIREMENTS:
1. Location: Extract the exact area name from the data. If unclear, mark as "Unknown Area"
2. Priority: Be VERY selective - only rank A if truly exceptional. Most properties should be B or C.
   - A: Only for prime locations with clear upside and minimal risk
   - B: Decent investments with some concerns
   - C: Problematic or overpriced properties (most should be here)
3. Prices: Format as €NUMBER with NO commas, NO dots (e.g., €1500000 not €1,500,000)
4. Reform cost (m2): Use the reform cost CSV data to determine cost PER SQUARE METER based on:
   - Property condition (new/good/needs renovation/poor)
   - Building type (villa/apartment/townhouse)
   - Age and features
   - Return ONLY the cost per m2 as €NUMBER (e.g., €3500), NOT total cost
5. Aimed sales price: Be CONSERVATIVE. Many properties won't achieve 25% margin. If overpriced, say so.
6. Macro location (1-10): Be CRITICAL. Most areas are 4-6. Only truly prime get 8+
   - 9-10: ONLY Son Vida, best parts of Port Andratx/Deià
   - 7-8: Good parts of Santa Ponsa, Bendinat, Portals
   - 5-6: Average coastal areas
   - 3-4: Inland, far from Palma
   - 1-2: Undesirable locations
7. Micro location (1-10): Look for PROBLEMS - busy roads, no privacy, bad neighbors, poor access
8. Business case: Focus on RISKS and PROBLEMS. What could go wrong? Why might this fail?
9. Email Draft: Ask HARD questions about:
   - Hidden defects and problems
   - Why is it still on the market?
   - Legal issues, debts, liens
   - Real reason for selling
   - Actual renovation costs (not optimistic estimates)
   - Problems with neighbors or community

BE SKEPTICAL. Most properties are overpriced. Find the flaws. Don't sugarcoat.

Return ONLY valid JSON with these exact keys in order:
Location, Link, ChatGPT Business Case, Nota Simple, Priority, License Yes/No, Project purchase price, Seaview, Comments, Total surface (m2) Metros construidos, Plot size, Price m2, Reform cost (m2), Aimed Sales Price without Real Estate Agent, Comparable Houses on the market 1, Comparable Houses on the market 2, Comparable Houses on the market 3, Macro location (1-10), Micro location (1-10), Sun direction, View, Building, Email Draft"""

    user_message = f"""Critically analyze this Mallorca property. Find the problems and risks:

Filtered API data (key metrics only):
{pyjson.dumps(filtered_api_data, indent=2)}

Extracted fields:
{pyjson.dumps(extracted_data, indent=2)}

Reform cost reference data:
{pyjson.dumps(reform_costs, indent=2)}

BE CRITICAL. Most properties are overpriced in Mallorca. Find what's wrong with this one.
Format all euro amounts as €NUMBER with no punctuation (€1500000 not €1,500,000).
For Reform cost (m2), use the CSV data to determine cost PER SQUARE METER only (e.g., €4000), not total cost.
Assume renovation will cost MORE than expected and take LONGER.
Be realistic about resale - who would actually buy this and why?

Return ONLY the JSON object, no markdown, no extra text."""

    try:
        response = client.chat.completions.create(
            model="o3-2025-04-16",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_completion_tokens=2000
        )
        
        content = response.choices[0].message.content
        # Clean potential markdown or extra text
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        
        ai_data = pyjson.loads(content.strip())
        
        # Merge with extracted data, preferring AI values for missing fields
        final_data = {}
        for col in COLUMNS:
            if col in ai_data and ai_data[col] != 'Info Missing':
                final_data[col] = ai_data[col]
            else:
                final_data[col] = extracted_data.get(col, 'Info Missing')
        
        return final_data
        
    except Exception as e:
        print(f"[ERROR] AI analysis failed: {e}")
        # Fallback: try with gpt-4o
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            content = response.choices[0].message.content
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            ai_data = pyjson.loads(content.strip())
            
            final_data = {}
            for col in COLUMNS:
                if col in ai_data and ai_data[col] != 'Info Missing':
                    final_data[col] = ai_data[col]
                else:
                    final_data[col] = extracted_data.get(col, 'Info Missing')
            
            return final_data
        except Exception as e2:
            print(f"[ERROR] Fallback AI also failed: {e2}")
            # Return extracted data as-is
            return {col: extracted_data.get(col, 'Info Missing') for col in COLUMNS}

def process_property(url, worksheet):
    print(f"[1/5] Processing property: {url}")
    
    # Load reform costs
    print(f"[2/5] Loading reform cost data...")
    reform_costs = load_reform_costs()
    
    # Extract property code
    property_code = extract_property_code(url)
    print(f"[3/5] Fetching Idealista API data for property {property_code}...")
    
    # Fetch from API
    api_data = fetch_idealista_api(property_code)
    if not api_data:
        print("[ERROR] Failed to fetch property data")
        return
    
    # Extract all available fields
    print(f"[4/5] Extracting fields from API response...")
    extracted_data = extract_all_idealista_fields(api_data, url)
    
    # Use AI to analyze and fill remaining fields
    print(f"[5/5] Running AI analysis to complete missing fields...")
    final_data = ai_analyze_property(api_data, extracted_data, reform_costs)
    
    # Build row in exact column order
    row = [final_data.get(col, 'Info Missing') for col in COLUMNS]
    
    # Write to sheet
    worksheet.append_row(row, value_input_option='USER_ENTERED')
    print(f"[DONE] Row written to Google Sheet!")
    
    # Print summary of filled fields
    filled_count = sum(1 for col in COLUMNS if final_data.get(col) != 'Info Missing')
    print(f"[STATS] Filled {filled_count}/{len(COLUMNS)} fields")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='RE Engine: Real Estate Analysis Tool')
    parser.add_argument('--url', type=str, required=True, help='Property listing URL to process')
    args = parser.parse_args()
    gc = get_gsheet_client()
    worksheet = get_worksheet(gc, SHEET_NAME, TAB_NAME)
    process_property(args.url, worksheet) 