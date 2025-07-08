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

def load_reform_costs():
    """Load reform costs from CSV file"""
    try:
        if os.path.exists(REFORM_COST_CSV):
            reform_df = pd.read_csv(REFORM_COST_CSV)
            return reform_df.to_dict('records')
        else:
            return []
    except Exception as e:
        print(f"[ERROR] Could not load reform costs: {e}")
        return []

def get_gsheet_client(service_account_info=None):
    """Get Google Sheets client using service account with proper error handling"""
    try:
        if service_account_info:
            # For Streamlit Cloud - use secrets
            if isinstance(service_account_info, dict) and service_account_info.get('type') == 'service_account':
                # Ensure private_key is properly formatted
                if 'private_key' in service_account_info:
                    private_key = service_account_info['private_key']
                    # Fix common private key formatting issues
                    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                        private_key = f"-----BEGIN PRIVATE KEY-----\n{private_key}\n-----END PRIVATE KEY-----\n"
                    elif '\\n' in private_key:
                        private_key = private_key.replace('\\n', '\n')
                    service_account_info['private_key'] = private_key
                
                gc = gspread.service_account_from_dict(service_account_info)
            else:
                raise ValueError("Invalid service account format. Please check your Streamlit secrets configuration.")
        else:
            # For local development - use file
            if os.path.exists('service_account.json'):
                gc = gspread.service_account(filename='service_account.json')
            else:
                raise ValueError("No service account file found. Please create service_account.json for local development.")
        return gc
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Sheets: {str(e)}")

def get_worksheet(gc, sheet_name, tab_name):
    try:
        sh = gc.open(sheet_name)
        worksheet = sh.worksheet(tab_name)
        return worksheet
    except Exception as e:
        raise Exception(f"Failed to access worksheet '{tab_name}' in sheet '{sheet_name}': {str(e)}")

def extract_property_code(url):
    return url.rstrip('/').split('/')[-1]

def fetch_idealista_api(property_code):
    if not IDEALISTA_API_KEY:
        raise ValueError("IDEALISTA_API_KEY is not set")
    
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
        return parsed
    except Exception as e:
        raise Exception(f"Could not parse Idealista API response: {e}")

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
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY is not set")
    
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Filter API data to remove verbose/unnecessary fields
    filtered_api_data = filter_api_data_for_ai(api_data)
    
    system_message = """You are an experienced Mallorca real estate investment analyst. Your job is to provide objective, realistic, and thorough property evaluations. Apply healthy skepticism while being fair and balanced in your assessments.

ANALYSIS REQUIREMENTS:
1. Location: Extract the exact area name from the data. If unclear, mark as "Unknown Area"
2. Priority: Evaluate objectively based on actual investment potential:
   - A: Excellent investment opportunity - strong fundamentals, good value, clear upside
   - B: Good investment with normal risks - solid property but may have some concerns
   - C: Poor investment - significant issues, overpriced, or high risk factors
3. Prices: Format as €NUMBER with NO commas, NO dots (e.g., €1500000 not €1,500,000)
4. Reform cost (m2): Use the reform cost CSV data to determine cost PER SQUARE METER based on:
   - Property condition (new/good/needs renovation/poor)
   - Building type (villa/apartment/townhouse)
   - Age and features
   - Return ONLY the cost per m2 as €NUMBER (e.g., €3500), NOT total cost
5. Aimed sales price: Be realistic about market conditions and property potential. Factor in:
   - Current market trends
   - Renovation costs and time
   - Location desirability
   - Property uniqueness
6. Macro location (1-10): Rate based on objective market data and desirability:
   - 9-10: Premium areas (Son Vida, best parts of Port Andratx/Deià)
   - 7-8: Highly desirable (Santa Ponsa, Bendinat, Portals, good coastal areas)
   - 5-6: Average desirable areas
   - 3-4: Less desirable but acceptable
   - 1-2: Undesirable locations
7. Micro location (1-10): Assess specific location factors:
   - Accessibility, privacy, noise levels, views, neighborhood quality
   - Traffic, parking, proximity to amenities
8. Business case: Provide balanced analysis covering:
   - Investment strengths and opportunities
   - Potential risks and challenges
   - Market positioning and competition
   - Realistic timeline and costs
9. Email Draft: Write professional inquiry focusing on:
   - Property condition and any defects
   - Legal status and documentation
   - Market positioning and pricing rationale
   - Renovation requirements and permits

BE OBJECTIVE: Evaluate each property on its own merits. Neither overly optimistic nor pessimistic. Base assessments on facts, location fundamentals, and realistic market conditions.

Return ONLY valid JSON with these exact keys in order:
Location, Link, ChatGPT Business Case, Nota Simple, Priority, License Yes/No, Project purchase price, Seaview, Comments, Total surface (m2) Metros construidos, Plot size, Price m2, Reform cost (m2), Aimed Sales Price without Real Estate Agent, Comparable Houses on the market 1, Comparable Houses on the market 2, Comparable Houses on the market 3, Macro location (1-10), Micro location (1-10), Sun direction, View, Building, Email Draft"""

    user_message = f"""Analyze this Mallorca property objectively and thoroughly:

Filtered API data (key metrics only):
{pyjson.dumps(filtered_api_data, indent=2)}

Extracted fields:
{pyjson.dumps(extracted_data, indent=2)}

Reform cost reference data:
{pyjson.dumps(reform_costs, indent=2)}

Provide a balanced, realistic assessment considering:
- Market conditions and comparable properties
- Location advantages and disadvantages
- Investment potential and risks
- Realistic renovation costs and timelines
- Actual market demand and buyer profile

Format all euro amounts as €NUMBER with no punctuation (€1500000 not €1,500,000).
For Reform cost (m2), use the CSV data to determine cost PER SQUARE METER only (e.g., €4000), not total cost.
Base your analysis on facts and realistic market expectations.

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
            raise Exception(f"AI analysis failed: {e}, Fallback also failed: {e2}")

def run_job(url, service_account_info=None):
    """Main function to process a property URL and write to Google Sheets"""
    try:
        # Load reform costs
        reform_costs = load_reform_costs()
        
        # Extract property code
        property_code = extract_property_code(url)
        
        # Fetch from API
        api_data = fetch_idealista_api(property_code)
        if not api_data:
            return {"success": False, "error": "Failed to fetch property data from Idealista API"}
        
        # Extract all available fields
        extracted_data = extract_all_idealista_fields(api_data, url)
        
        # Use AI to analyze and fill remaining fields
        final_data = ai_analyze_property(api_data, extracted_data, reform_costs)
        
        # Get Google Sheets client and worksheet
        gc = get_gsheet_client(service_account_info)
        worksheet = get_worksheet(gc, SHEET_NAME, TAB_NAME)
        
        # Build row in exact column order
        row = [final_data.get(col, 'Info Missing') for col in COLUMNS]
        
        # Write to sheet
        worksheet.append_row(row, value_input_option='USER_ENTERED')
        
        # Count filled fields
        filled_count = sum(1 for col in COLUMNS if final_data.get(col) != 'Info Missing')
        
        return {
            "success": True, 
            "message": f"Successfully processed property and wrote to Google Sheet! Filled {filled_count}/{len(COLUMNS)} fields.",
            "filled_fields": filled_count,
            "total_fields": len(COLUMNS),
            "property_code": property_code
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)} 