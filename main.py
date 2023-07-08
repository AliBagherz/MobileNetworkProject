from flask import Flask, request, jsonify, redirect
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

import downloader
import sqlite3

app = Flask(__name__)


@app.route('/analyse_app', methods=['GET'])
def analyse_app():
    package_name = request.args.get('package_id')
    downloader.download_apk(package_name)
    package_path = f"output/{package_name}.apk"
    multipart_data = MultipartEncoder(
        fields={'file': (package_path, open(package_path, 'rb'), 'application/octet-stream')})
    response = requests.post("http://localhost:8000/api/v1/upload", data=multipart_data,
                             headers={"Content-Type": multipart_data.content_type,
                                      "X-Mobsf-Api-Key": "062cc98851d7910281c95aa8f7c34bc1ccc5695eea2564d37031e0c6669ba58d"})
    with sqlite3.connect("data.db") as con:
        cur = con.cursor()
        cur.execute(f"INSERT INTO Analysis (file, hash) VALUES ('{package_name}.apk', '{response.json()['hash']}')")
        con.commit()
    requests.post("http://localhost:8000/api/v1/scan",
                  data={"scan_type": "apk", "file_name": package_name + ".apk",
                        "hash": response.json()["hash"]},
                  headers={
                      "X-Mobsf-Api-Key": "062cc98851d7910281c95aa8f7c34bc1ccc5695eea2564d37031e0c6669ba58d"})
    return redirect(f"/get_pdf?package_id={package_name}")


@app.route('/get_pdf', methods=['GET'])
def get_pdf():
    package_name = request.args.get('package_id')
    with sqlite3.connect("data.db") as con:
        cur = con.cursor()
        hashes = cur.execute(f"SELECT hash FROM Analysis WHERE file = '{package_name}.apk' order by -id")
        hashes = hashes.fetchall()

    response = requests.post("http://localhost:8000/api/v1/download_pdf",
                             data={"hash": hashes[0]},
                             headers={
                                 "X-Mobsf-Api-Key": "062cc98851d7910281c95aa8f7c34bc1ccc5695eea2564d37031e0c6669ba58d"})

    with open(f'reports/{package_name}.pdf', 'wb') as f:
        f.write(response.content)
    return jsonify({"Response": "PDF saved."})


if __name__ == '__main__':
    connection = sqlite3.connect("data.db")
    cursor = connection.cursor()
    try:
        cursor.execute(
            "CREATE TABLE Analysis(id INTEGER PRIMARY KEY AUTOINCREMENT, file text NOT NULL , hash NOT NULL)")
    except Exception as err:
        print(err)
    app.run(port=8001)
