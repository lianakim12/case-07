from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
import os

load_dotenv()

CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
STORAGE_ACCOUNT_URL = os.environ.get("STORAGE_ACCOUNT_URL")
CONTAINER_NAME = os.environ.get("IMAGES_CONTAINER", "lanternfly-images-zs7554kz")

app = Flask(__name__)

ACCOUNT_NAME = "ds2022"
CONTAINER_NAME = "lanternfly-images-zs7554kz"

bsc = BlobServiceClient.from_connection_string(CONNECTION_STRING)
cc = bsc.get_container_client(CONTAINER_NAME)

@app.post("/api/v1/upload")
def upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file part in the request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"ok": False, "error": "No file selected."}), 400

    sanitized_filename = secure_filename(file.filename)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    blob_name = f"{timestamp}-{sanitized_filename}"

    blob_client = bsc.get_blob_client(container=CONTAINER_NAME, blob=blob_name)

    try:
        blob_client.upload_blob(
            file.stream,
            overwrite=True,
            content_settings=ContentSettings(content_type=file.content_type),
        )
    except Exception as e:
        return jsonify({"ok": False, "error": f"Upload failed: {str(e)}"}), 500

    blob_url = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}"
    return jsonify({"ok": True, "url": blob_url}), 200

@app.get("/api/v1/gallery")
def gallery_api():
    try:
        blob_list = cc.list_blobs()
        gallery_urls = []
        for blob in blob_list:
            # Construct the public URL
            public_url = f"{cc.url}/{blob.name}"
            gallery_urls.append(public_url)
        return jsonify({"ok": True, "gallery": gallery_urls}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/v1/health")
def health_check():
    return jsonify({"ok": True, "status": "healthy"}), 200

@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)