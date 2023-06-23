import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
)
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter

if os.name == "nt":
    UPLOAD_FOLDER = f"{str(os.getcwd())}\\uploads"
    DOWNLOAD_FOLDER = f"{str(os.getcwd())}\\downloads"
elif os.name == "posix":
    UPLOAD_FOLDER = f"{str(os.getcwd())}/uploads"
    DOWNLOAD_FOLDER = f"{str(os.getcwd())}/downloads"

ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DOWNLOAD_FOLDER"] = DOWNLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 64 * 1000 * 1000


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    delete_files()
    return render_template("index.html")


@app.route("/split", methods=["POST"])
def split_pdf():
    if "pdf_file" not in request.files:
        return render_template("index.html", error_message="No file selected.")

    file = request.files["pdf_file"]

    if file.filename == "":
        return render_template("index.html", error_message="No file selected.")

    if not allowed_file(file.filename):
        return render_template(
            "index.html", error_message="Invalid file format. Only PDF files allowed."
        )

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"], secure_filename(file.filename)
    )
    file.save(file_path)

    try:
        pdf = PdfReader(file_path)

        # Split the PDF into individual pages
        for page_number in range(len(pdf.pages)):
            output = PdfWriter()
            output.insert_page(pdf.pages[page_number], page_number + 1)

            # Save each page as a separate PDF
            output_filename = f"page_{page_number + 1}.pdf"
            output_path = os.path.join(app.config["DOWNLOAD_FOLDER"], output_filename)
            with open(output_path, "wb") as output_file:
                output.write(output_file)
                output_file.close()

        delete_uploads()
        return redirect(url_for("download"))

    except Exception as e:
        return render_template(
            "index.html",
            error_message="An unexpected error occurred.",
        )


@app.route("/merge", methods=["POST"])
def merge_pdf():
    uploaded_files = request.files.getlist("pdf_files[]")

    if len(uploaded_files) < 2:
        return render_template(
            "index.html", error_message="Please select at least two PDF files."
        )

    file_paths = []
    for file in uploaded_files:
        if file.filename == "":
            return render_template("index.html", error_message="No file selected.")

        if not allowed_file(file.filename):
            return render_template(
                "index.html",
                error_message="Invalid file format. Only PDF files are allowed.",
            )

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"], secure_filename(file.filename)
        )
        file.save(file_path)
        file_paths.append(file_path)

    try:
        output = PdfWriter()
        output_path = os.path.join(app.config["DOWNLOAD_FOLDER"], "merged.pdf")

        # Merge the PDF files
        for file_path in list(reversed(file_paths)):
            pdf = PdfReader(file_path)
            for page_number in range(len(pdf.pages)):
                output.add_page(pdf._get_page(page_number))

        with open(output_path, "wb") as output_file:
            output.write(output_file)
            output_file.close()

        delete_uploads()
        return redirect(url_for("download"))

    except Exception as e:
        return render_template(
            "index.html",
            error_message="An unexpected error occurred.",
        )


@app.route("/download", methods=["GET"])
def download():
    files = os.listdir(app.config["DOWNLOAD_FOLDER"])
    return render_template("download.html", files=files)


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory(
        app.config["DOWNLOAD_FOLDER"], filename, as_attachment=True
    )


@app.route("/about")
def about():
    return render_template("about.html")


def delete_uploads():
    directory = app.config["UPLOAD_FOLDER"]
    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


def delete_downloads():
    directory = app.config["DOWNLOAD_FOLDER"]
    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


def delete_files():
    delete_uploads()
    delete_downloads()
