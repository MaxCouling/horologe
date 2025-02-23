from flask import Flask, render_template
from get_time import get_show_info

app = Flask(__name__)

@app.route('/')
def index():
    shows_to_display = []
    for title in ["Severance", "Invincible"]:
        shows_to_display.append(get_show_info(title))

    return render_template('index.html', featured_shows=shows_to_display)

if __name__ == '__main__':
    app.run(debug=True)