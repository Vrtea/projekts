from flask import Flask, render_template, request, redirect, url_for, g
from flask_babel import Babel, _  # Importing Babel for translations
import pandas as pd
import sqlite3
import plotly.express as px
import os
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64

# Create Flask app and set up configuration
app = Flask(__name__)

# Configure Babel for translations
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
babel = Babel(app)

# Database setup
DATABASE = 'transport.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS emissions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            city TEXT, 
                            transport_type TEXT, 
                            co2_emission REAL, 
                            passengers INTEGER)''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            df = pd.read_csv(filepath)
            with sqlite3.connect(DATABASE) as conn:
                df.to_sql('emissions', conn, if_exists='append', index=False)
            return redirect(url_for('dashboard'))
    return render_template('upload.html')

@app.route('/dashboard')
def dashboard():
    with sqlite3.connect(DATABASE) as conn:
        df = pd.read_sql_query('SELECT * FROM emissions', conn)
    
    # Bar chart for CO₂ emissions
    fig1 = px.bar(df, x='city', y='co2_emission', color='transport_type', title='CO₂ emisijas pēc transporta veida')
    graph1 = fig1.to_html(full_html=False)
    
    # Histogram for passenger distriSabiedriskā transporta ietekmes analīzebution
    plt.figure(figsize=(8, 6))
    sns.histplot(df['passengers'], bins=10, kde=True)
    plt.xlabel('Pasažieru skaits')
    plt.ylabel('Biežums')
    plt.title('Pasažieru izplatīšana')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    histogram = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return render_template('dashboard.html', graph1=graph1, histogram=histogram)

@app.route('/filter', methods=['GET'])
def filter_data():
    transport_type = request.args.get('transport_type', default='All')
    with sqlite3.connect(DATABASE) as conn:
        if transport_type == 'All':
            df = pd.read_sql_query('SELECT * FROM emissions', conn)
        else:
            df = pd.read_sql_query('SELECT * FROM emissions WHERE transport_type = ?', conn, params=(transport_type,))
    
    fig = px.bar(df, x='city', y='co2_emission', color='transport_type', title=f'Filtrētās CO₂ emisijas ({transport_type})')
    graph = fig.to_html(full_html=False)
    
    return render_template('filter.html', graph=graph)

@app.route('/set_language/<lang>')
def set_language(lang):
    return redirect(url_for('index', lang=lang))

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'lv']:
        g.lang = lang
        return redirect(request.referrer)  # Redirect to the page the user was on
    return redirect('/')
