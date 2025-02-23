from flask import Flask, render_template, url_for
from get_time import get_show_info
import os

app = Flask(__name__)
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_DESTINATION'] = 'docs'  # GitHub Pages looks for docs folder

@app.route('/')
def index():
    shows_to_display = []
    for title in ["Severance", "Invincible"]:
        shows_to_display.append(get_show_info(title))
    return render_template('index.html', featured_shows=shows_to_display)

@app.route('/static/<path:filename>')
def static_files(filename):
    return url_for('static', filename=filename)

if __name__ == '__main__':
    app.run(debug=True)