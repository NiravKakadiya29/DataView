import os
import pandas as pd
import requests
import io
import chardet
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from ydata_profiling import ProfileReport

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def detect_encoding(filepath):
    """Detect file encoding using chardet."""
    with open(filepath, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result["encoding"]

def generate_report(data, filename):
    """Generate ProfileReport and save as HTML."""
    report = ProfileReport(data, title="Data Profiling Report")
    report_path = os.path.join("static", filename)
    report.to_file(report_path)
    return report_path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = None
        filename = "report.html"

        # Handle File Upload
        file = request.files.get("file")
        url = request.form.get("url")

        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename))
            file.save(filepath)

            # Detect encoding and read CSV
            encoding = detect_encoding(filepath)
            data = pd.read_csv(filepath, encoding=encoding)

        elif url:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    # Detect encoding from URL response
                    raw_data = response.content
                    detected_encoding = chardet.detect(raw_data)["encoding"]
                    
                    # Read CSV with detected encoding
                    data = pd.read_csv(io.StringIO(response.text), encoding=detected_encoding)
                else:
                    return render_template("index.html", error="Failed to fetch CSV from URL.")
            except Exception as e:
                return render_template("index.html", error=f"Error fetching URL: {e}")

        if data is not None:
            report_path = generate_report(data, filename)
            return redirect(url_for("report"))

    return render_template("index.html")

@app.route("/report")
def report():
    return render_template("report.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # For Render deployment
    app.run(debug=True, host="0.0.0.0", port=port)
