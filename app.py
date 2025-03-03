import os
import pandas as pd
import requests
import io
import chardet
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from ydata_profiling import ProfileReport

app = Flask(__name__)

# Ensure the static folder exists
os.makedirs("static", exist_ok=True)

app.config["UPLOAD_FOLDER"] = "/tmp/"

def detect_encoding(filepath):
    """Detect file encoding using chardet."""
    with open(filepath, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result["encoding"]

def generate_report(data, filename):
    """Generate ProfileReport with all chunks combined."""
    report = ProfileReport(data, title="Complete Data Profiling Report", minimal=True)
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

            # Detect encoding and read CSV in chunks
            encoding = detect_encoding(filepath)
            data_iter = pd.read_csv(filepath, encoding=encoding, chunksize=5000)  # Read in chunks
            
            # Process all chunks by concatenating them
            data = pd.concat(data_iter, ignore_index=True)

            # Remove file after processing
            os.remove(filepath)

        elif url:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    raw_data = response.content
                    detected_encoding = chardet.detect(raw_data)["encoding"]
                    
                    # Read CSV with detected encoding in chunks
                    data_iter = pd.read_csv(io.StringIO(response.text), encoding=detected_encoding, chunksize=5000)

                    # Process all chunks by concatenating them
                    data = pd.concat(data_iter, ignore_index=True)
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
