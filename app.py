import pymysql
pymysql.install_as_MySQLdb()
import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from openai import OpenAI
import copy

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key_here')
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('JAWSDB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    revenue = db.Column(db.String(20), nullable=False)
    market_cap = db.Column(db.String(20), nullable=False)
    summary = db.Column(db.String(500), nullable=False)
    categories = db.Column(db.String(200), nullable=False)
    days_ago = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

CHECKLIST = [
    "financial stability",
    "legal compliance",
    "operational efficiency"
]

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def summarize_document(text):
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
    if value.endswith('K'):
        return float(value[1:-1]) * 1_000
    elif value.endswith('M'):
        return float(value[1:-1]) * 1_000_000
    elif value.endswith('B'):
        return float(value[1:-1]) * 1_000_000_000
    else:
        return float(value[1:])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/due_diligence', methods=['GET', 'POST'])
def due_diligence():
    session['processing_status'] = []
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            try:
                session['processing_status'].append("Uploading file...")
                session.modified = True
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

@app.route('/get_processing_status')
def get_processing_status():
    return jsonify({'status': session.get('processing_status', [])})

@app.route('/download-example-file')
def download_example_file():
    return send_from_directory(directory='.', path='acme_company_report.pdf', as_attachment=True)

@app.route('/matchmaking', methods=['GET'])
def matchmaking():
    selected_categories = request.args.getlist('filter')  # Get a list of selected filters
    sort_by = request.args.get('sort_by')

    # Fetch all companies from the database
    all_companies = Company.query.all()

    # Convert SQLAlchemy results to a list of dictionaries
    companies_list = [
        {
            'name': company.name,
            'revenue': company.revenue,
            'market_cap': company.market_cap,
            'summary': company.summary,
            'categories': [cat.strip() for cat in company.categories.split(',')],
            'days_ago': company.days_ago,
            'country': company.country
        }
        for company in all_companies
    ]

    # Sort all companies first based on the selected sort option
    if sort_by == 'revenue':
        companies_list.sort(key=lambda x: parse_value(x['revenue']), reverse=True)
    elif sort_by == 'market_cap':
        companies_list.sort(key=lambda x: parse_value(x['market_cap']), reverse=True)
    elif sort_by == 'recently_posted':
        companies_list.sort(key=lambda x: x['days_ago'])

    # Filter companies based on selected categories
    if selected_categories and (selected_categories[0] or len(selected_categories) > 1):
        matching_companies = [
            company for company in companies_list
            if any(cat in company['categories'] for cat in selected_categories)
        ]
    else:
        matching_companies = copy.deepcopy(companies_list)  # No filters; return all

    # Count matching companies
    matching_count = len(matching_companies)

    # Prepare a set of categories for the dropdown
    categories = sorted(set(cat for company in companies_list for cat in company['categories']))

    return render_template('matchmaking.html', companies=matching_companies, categories=categories, 
                           selected_categories=selected_categories, sort_by=sort_by, 
                           matching_count=matching_count)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)