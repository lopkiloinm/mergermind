import pymysql
pymysql.install_as_MySQLdb()
import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from openai import OpenAI
import copy

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Get the database URL from the environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('JAWSDB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define your Company model
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    revenue = db.Column(db.String(20), nullable=False)
    market_cap = db.Column(db.String(20), nullable=False)
    summary = db.Column(db.String(500), nullable=False)
    categories = db.Column(db.String(200), nullable=False) # Consider using a separate table for categories if it's a complex structure
    days_ago = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(100), nullable=False)

# Create the database and tables (run just once)
with app.app_context():
    db.create_all()

# Static data for matchmaking
COMPANIES = [
    {"name": "Alpha Corp", "revenue": "$1M", "market_cap": "$10M", "summary": "A leading producer of high-quality consumer electronics.", "categories": ["Electronics", "Consumer Goods"], "days_ago": 5, "country": "USA"},
    {"name": "Beta LLC", "revenue": "$5M", "market_cap": "$20M", "summary": "Innovative software solutions for small businesses and startups.", "categories": ["Software", "Technology"], "days_ago": 10, "country": "Canada"},
    {"name": "Gamma Inc.", "revenue": "$500K", "market_cap": "$15M", "summary": "Specializing in logistics and supply chain management.", "categories": ["Logistics", "Supply Chain"], "days_ago": 15, "country": "UK"},
    {"name": "Delta Solutions", "revenue": "$2M", "market_cap": "$30M", "summary": "Consulting and technology services for financial institutions.", "categories": ["Consulting", "Finance"], "days_ago": 3, "country": "Australia"},
    {"name": "Epsilon Tech", "revenue": "$8M", "market_cap": "$45M", "summary": "Developing cutting-edge AI tools for businesses.", "categories": ["Artificial Intelligence", "Software"], "days_ago": 7, "country": "Germany"},
    {"name": "Zeta Innovations", "revenue": "$3M", "market_cap": "$25M", "summary": "Creating sustainable energy solutions.", "categories": ["Energy", "Sustainability"], "days_ago": 12, "country": "Sweden"},
    {"name": "Eta Services", "revenue": "$6M", "market_cap": "$50M", "summary": "Full-service agency for digital marketing.", "categories": ["Marketing", "Advertising"], "days_ago": 20, "country": "USA"},
    {"name": "Theta Holdings", "revenue": "$4M", "market_cap": "$35M", "summary": "Privately held investment firm focused on startups.", "categories": ["Investing", "Finance"], "days_ago": 25, "country": "Canada"},
    {"name": "Iota Pharmaceuticals", "revenue": "$7M", "market_cap": "$60M", "summary": "Biotech firm developing innovative medicines.", "categories": ["Pharmaceutical", "Health"], "days_ago": 30, "country": "Switzerland"},
    {"name": "Kappa Logistics", "revenue": "$9M", "market_cap": "$70M", "summary": "Providing logistics solutions for global trade.", "categories": ["Logistics", "Shipping"], "days_ago": 18, "country": "China"},
    {"name": "Lambda Retail", "revenue": "$1.5M", "market_cap": "$15M", "summary": "Online marketplace for organic products.", "categories": ["E-commerce", "Retail"], "days_ago": 21, "country": "USA"},
    {"name": "Mu Media", "revenue": "$2.5M", "market_cap": "$22M", "summary": "Creating engaging content for brands.", "categories": ["Media", "Content Creation"], "days_ago": 14, "country": "Australia"},
    {"name": "Nu Health", "revenue": "$10M", "market_cap": "$90M", "summary": "Health and wellness products to consumers.", "categories": ["Health", "Consumer Goods"], "days_ago": 8, "country": "UK"},
    {"name": "Xi Financial", "revenue": "$8M", "market_cap": "$65M", "summary": "Financial advisory services for high net worth individuals.", "categories": ["Finance", "Consulting"], "days_ago": 11, "country": "Canada"},
    {"name": "Omicron Transportation", "revenue": "$2.1M", "market_cap": "$18M", "summary": "Specialized in freight transport and logistics.", "categories": ["Logistics", "Transportation"], "days_ago": 19, "country": "Germany"},
    {"name": "Pi Tech", "revenue": "$4.5M", "market_cap": "$40M", "summary": "AI-driven solutions for healthcare.", "categories": ["Artificial Intelligence", "Health"], "days_ago": 6, "country": "USA"},
    {"name": "Rho Developments", "revenue": "$3.2M", "market_cap": "$28M", "summary": "Real estate development and management.", "categories": ["Real Estate", "Investment"], "days_ago": 4, "country": "Australia"},
    {"name": "Sigma Manufacturing", "revenue": "$5.5M", "market_cap": "$50M", "summary": "Manufacturing parts for the automotive industry.", "categories": ["Manufacturing", "Automotive"], "days_ago": 12, "country": "China"},
    {"name": "Tau Industries", "revenue": "$9.5M", "market_cap": "$80M", "summary": "Producing components for renewable energy systems.", "categories": ["Energy", "Manufacturing"], "days_ago": 15, "country": "Germany"},
    {"name": "Upsilon Solutions", "revenue": "$11M", "market_cap": "$100M", "summary": "Providing cloud computing solutions.", "categories": ["Cloud Computing", "Software"], "days_ago": 22, "country": "USA"},
    {"name": "Phi Robotics", "revenue": "$1.8M", "market_cap": "$16M", "summary": "Developing robotic systems for automation.", "categories": ["Robotics", "Technology"], "days_ago": 13, "country": "Japan"},
    {"name": "Chi Fintech", "revenue": "$3.5M", "market_cap": "$30M", "summary": "Digital financial services and solutions.", "categories": ["Fintech", "Technology"], "days_ago": 9, "country": "Canada"},
    {"name": "Psi Analytics", "revenue": "$7.2M", "market_cap": "$55M", "summary": "Data analytics for businesses to improve performance.", "categories": ["Analytics", "Consulting"], "days_ago": 27, "country": "USA"},
    {"name": "Omega Biotech", "revenue": "$6.8M", "market_cap": "$45M", "summary": "Research and development of biotech solutions.", "categories": ["Biotech", "Health"], "days_ago": 16, "country": "Germany"},
    {"name": "AlphaTech", "revenue": "$12M", "market_cap": "$120M", "summary": "Leading provider of enterprise software solutions.", "categories": ["Software", "Technology"], "days_ago": 5, "country": "USA"},
    {"name": "BetaRenewables", "revenue": "$8M", "market_cap": "$50M", "summary": "Innovative renewable energy solutions.", "categories": ["Energy", "Sustainability"], "days_ago": 4, "country": "Canada"},
    {"name": "GammaHealth", "revenue": "$9M", "market_cap": "$80M", "summary": "Healthcare products focusing on wellness.", "categories": ["Health", "Consumer Goods"], "days_ago": 11, "country": "Australia"},
    {"name": "DeltaRetailers", "revenue": "$5M", "market_cap": "$40M", "summary": "Bringing local products to the global market.", "categories": ["E-commerce", "Retail"], "days_ago": 18, "country": "USA"},
    {"name": "EpsilonVentures", "revenue": "$7.5M", "market_cap": "$75M", "summary": "Venture capital firm investing in tech startups.", "categories": ["Investing", "Finance"], "days_ago": 22, "country": "UK"},
    {"name": "ZetaAI", "revenue": "$10M", "market_cap": "$90M", "summary": "Leveraging AI to enhance business processes.", "categories": ["Artificial Intelligence", "Software"], "days_ago": 10, "country": "Germany"},
    {"name": "EtaMarketing", "revenue": "$3M", "market_cap": "$25M", "summary": "Specialized marketing solutions for brands.", "categories": ["Marketing", "Advertising"], "days_ago": 14, "country": "USA"},
    {"name": "ThetaHealthCo", "revenue": "$2.5M", "market_cap": "$20M", "summary": "Nutritional supplements and wellness products.", "categories": ["Health", "Consumer Goods"], "days_ago": 17, "country": "Australia"},
    {"name": "IotaLogistics", "revenue": "$6M", "market_cap": "$55M", "summary": "Helping businesses streamline their supply chains.", "categories": ["Logistics", "Transportation"], "days_ago": 30, "country": "China"},
    {"name": "KappaTech", "revenue": "$9M", "market_cap": "$70M", "summary": "Innovative tech solutions for modern businesses.", "categories": ["Technology", "Software"], "days_ago": 19, "country": "Sweden"},
    {"name": "LambdaInnovations", "revenue": "$4M", "market_cap": "$37M", "summary": "Creating new technologies for a sustainable future.", "categories": ["Innovation", "Sustainability"], "days_ago": 24, "country": "USA"},
    {"name": "MuGames", "revenue": "$6.5M", "market_cap": "$60M", "summary": "Developing engaging mobile applications and games.", "categories": ["Gaming", "Entertainment"], "days_ago": 5, "country": "Canada"},
    {"name": "NuElectric", "revenue": "$8.5M", "market_cap": "$85M", "summary": "Electric vehicle charging solutions and infrastructure.", "categories": ["Energy", "Transportation"], "days_ago": 20, "country": "Germany"},
    {"name": "XiGreen", "revenue": "$10.5M", "market_cap": "$110M", "summary": "Sustainable practices for waste management.", "categories": ["Environment", "Sustainability"], "days_ago": 6, "country": "UK"},
    {"name": "OmicronAgro", "revenue": "$7M", "market_cap": "$60M", "summary": "Sustainable agricultural products and services.", "categories": ["Agriculture", "Sustainability"], "days_ago": 8, "country": "Netherlands"},
    {"name": "PiFashion", "revenue": "$3.8M", "market_cap": "$32M", "summary": "Eco-friendly fashion and apparel.", "categories": ["Retail", "Sustainability"], "days_ago": 15, "country": "USA"},
    {"name": "RhoCrafts", "revenue": "$2M", "market_cap": "$18M", "summary": "Handcrafted goods marketplace supporting local artisans.", "categories": ["E-commerce", "Handmade"], "days_ago": 12, "country": "Canada"},
    {"name": "SigmaEvents", "revenue": "$4.2M", "market_cap": "$36M", "summary": "Event planning and management solutions.", "categories": ["Event Management", "Consulting"], "days_ago": 14, "country": "Australia"},
    {"name": "TauRealty", "revenue": "$5.2M", "market_cap": "$38M", "summary": "Real estate brokerage focusing on sustainable projects.", "categories": ["Real Estate", "Sustainability"], "days_ago": 3, "country": "USA"},
    {"name": "UpsilonTravel", "revenue": "$6.3M", "market_cap": "$55M", "summary": "Travel agency specializing in eco-friendly tourism.", "categories": ["Travel", "Sustainability"], "days_ago": 18, "country": "Germany"},
    {"name": "PhiFood", "revenue": "$9.1M", "market_cap": "$75M", "summary": "Gourmet food delivery service with local sourcing.", "categories": ["Food", "E-commerce"], "days_ago": 11, "country": "UK"},
    {"name": "ChiDesign", "revenue": "$4.6M", "market_cap": "$42M", "summary": "Design studio focused on sustainable architecture.", "categories": ["Design", "Architecture"], "days_ago": 7, "country": "Sweden"},
    {"name": "PsiSecurity", "revenue": "$8M", "market_cap": "$72M", "summary": "Providing advanced security systems for businesses.", "categories": ["Security", "Technology"], "days_ago": 5, "country": "USA"},
    {"name": "OmegaMining", "revenue": "$7.4M", "market_cap": "$63M", "summary": "Mining operations focusing on ethical practices.", "categories": ["Mining", "Sustainability"], "days_ago": 4, "country": "Canada"},
    {"name": "AlphaMobility", "revenue": "$6.9M", "market_cap": "$59M", "summary": "Solutions for personal and public transportation.", "categories": ["Transportation", "Technology"], "days_ago": 9, "country": "France"}
]

# Define your checklist items for Due Diligence
CHECKLIST = [
    "financial stability",
    "legal compliance",
    "operational efficiency"
]

def extract_text_from_pdf(file_path):
    """Extract text from the PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def summarize_document(text):
    """Summarize the document text using OpenAI."""
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Please summarize the key points of the following document:\n\n" + text}
        ],
        response_format={"type": "text"},
        temperature=0.5,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    if response.choices and len(response.choices) > 0:
        return response.choices[0].message.content.strip()
    else:
        raise ValueError("No valid summary received from OpenAI API.")

def analyze_with_openai(summary, checklist_item):
    """Analyze the summary against checklist items using OpenAI."""
    prompt = f"Does the document's key points indicate meeting the {checklist_item} criteria?"
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt + "\n\nSummary:\n" + summary}
        ],
        response_format={"type": "text"},
        temperature=0.1,
        max_tokens=15000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    if response.choices and len(response.choices) > 0:
        return response.choices[0].message.content.strip()
    else:
        raise ValueError("No valid response received from OpenAI API.")

def parse_value(value):
    """Convert revenue or market cap string to a float."""
    if value.endswith('K'):
        return float(value[1:-1]) * 1_000
    elif value.endswith('M'):
        return float(value[1:-1]) * 1_000_000
    elif value.endswith('B'):
        return float(value[1:-1]) * 1_000_000_000
    else:
        return float(value[1:])  # Handle case where there's no suffix

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/due_diligence', methods=['GET', 'POST'])
def due_diligence():
    session['processing_status'] = []  # Clear previous status
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        # Ensure a valid PDF file
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                session['processing_status'].append("Extracting text from PDF...")
                text = extract_text_from_pdf(file_path)

                session['processing_status'].append("Summarizing document...")
                summary = summarize_document(text)

                results = {}
                for item in CHECKLIST:
                    session['processing_status'].append(f"Analyzing: {item}...")
                    analysis_result = analyze_with_openai(summary, item)
                    results[item] = analysis_result

                session['processing_status'].append("Analysis completed!")
                return render_template('results.html', results=results)

            except Exception as e:
                print(f"An error occurred: {e}")
                return "An error occurred during processing", 500
        else:
            return "Invalid file type. Please upload a PDF.", 400

    return render_template('due_diligence.html')

@app.route('/download-example-file')
def download_example_file():
    # Ensure this path correctly matches where your example file is stored
    return send_from_directory(directory='.', path='acme_company_report.pdf', as_attachment=True)

@app.route('/matchmaking', methods=['GET'])
def matchmaking():
    selected_categories = request.args.getlist('filter')  # Get a list of selected filters
    sort_by = request.args.get('sort_by')

    # Sort all companies first based on the selected sort option
    if sort_by == 'revenue':
        COMPANIES.sort(key=lambda x: parse_value(x['revenue']), reverse=True)
    elif sort_by == 'market_cap':
        COMPANIES.sort(key=lambda x: parse_value(x['market_cap']), reverse=True)
    elif sort_by == 'recently_posted':
        COMPANIES.sort(key=lambda x: x['days_ago'])

    # Separate already sorted companies into those that match the filter and those that don't
    if selected_categories:
        matching_companies = [company for company in COMPANIES if any(cat in company['categories'] for cat in selected_categories)]
        #non_matching_companies = [company for company in COMPANIES if all(cat not in company['categories'] for cat in selected_categories)]
        # Ensure matching companies come first
        filtered_companies = matching_companies #+ non_matching_companies
    else:
        filtered_companies = copy.deepcopy(COMPANIES)

    # Prepare a set of categories for the dropdown
    categories = sorted(set(cat for company in COMPANIES for cat in company['categories']))
    
    return render_template('matchmaking.html', companies=filtered_companies, categories=categories, selected_categories=selected_categories, sort_by=sort_by)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)