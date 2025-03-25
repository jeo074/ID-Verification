'''
bash:
pip install flask flask-cors boto3 psycopg2 google-cloud-vision opencv-python==4.5.5.62 dotenv
'''

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import boto3
from google.cloud import vision
import cv2
import psycopg2
import traceback
import os
import re
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# aws rekognition configuration
load_dotenv()
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

rekognition = boto3.client(
    "rekognition",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

# google vision configuration
google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(google_creds_path)
vision_client = vision.ImageAnnotatorClient()

# Load PostgreSQL Credentials
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT")
)

# upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/validate", methods=["POST"])
def validate_images():
    try:
        # save uploaded files
        id_file = request.files["id_image"]
        selfie_file = request.files["selfie_image"]
        id_path = os.path.join(UPLOAD_DIR, id_file.filename)
        selfie_path = os.path.join(UPLOAD_DIR, selfie_file.filename)

        id_file.save(id_path)
        selfie_file.save(selfie_path)

        # step 1: extract id details using google vision ocr
        extracted_data = extract_id_details(id_path)
        if not extracted_data:
            return jsonify({"status": "Failed", "message": "Invalid ID or ID not clear."})

        # step 2: compare id and selfie using aws rekognition
        is_same_person, similarity = compare_faces(id_path, selfie_path)
        if not is_same_person:
            return jsonify({"status": "Failed", "message": "Face mismatch between ID and selfie."})

        # step 3: validate id template
        is_valid_id = validate_id_template(id_path)
        if not is_valid_id:
            return jsonify({"status": "Failed", "message": "Invalid ID template."})

        # step 4: store data using postgresql
        store_sql(extracted_data, is_same_person, similarity)
        extracted_data['is_same_person'] = str(is_same_person)
        extracted_data['similarity'] = f"{round(similarity, 2)}%"

        print("Success")
        return jsonify({"status": "Success", "data": extracted_data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "Error", "message": str(e)})


def compare_faces(id_path, selfie_path):
    with open(id_path, "rb") as id_image, open(selfie_path, "rb") as selfie_image:
        try:
            response = rekognition.compare_faces(
                SourceImage={"Bytes": id_image.read()},
                TargetImage={"Bytes": selfie_image.read()}
            )
            is_same_person = len(response["FaceMatches"]) > 0
            if is_same_person:
                similarity = 0
                for face in response["FaceMatches"]:
                    if similarity < face["Similarity"]:
                        similarity = face["Similarity"]
            return {is_same_person, similarity}
        except:
            raise Exception("Failed comparing faces! Please try again.")

def validate_id_template(id_path):
    # decode template image
    template_path = os.path.abspath('.') + r"\template\pnid_template.jpg"
    template_image = cv2.imread(template_path)
    input_image = cv2.imread(id_path)

    # feature matching with opencv
    sift = cv2.SIFT_create()
    template_image = cv2.normalize(template_image, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
    input_image = cv2.normalize(input_image, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
    kp1, des1 = sift.detectAndCompute(template_image, None)
    kp2, des2 = sift.detectAndCompute(input_image, None)
    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
    matches = bf.match(des1, des2)
    return len(matches) > 50


def extract_id_details(id_path):
    with open(id_path, "rb") as image_file:
        content = image_file.read()

    features = [{'type_': vision.Feature.Type.TEXT_DETECTION}]
    response = vision_client.annotate_image({
        'image': {'content': content},
        'features': features
    })
    texts = response.text_annotations

    if "PAMBANSANG PAGKAKAKILANLAN" not in str(texts):
        return None

    id_pattern = r'(\d{4}-\d{4}-\d{4}-\d{4})'
    lname_pattern = r'Last Name\n([A-ZÑñ ]+)\n'
    fname_pattern = r'Given Names\n([A-ZÑñ ]+)\n'
    mname_pattern = r'Middle Name\n([A-ZÑñ ]+)\n'
    dob_pattern = r'Date of Birth\n([A-Z ]+\d{2}, \d{4})'

    id_match = None
    lname_match = None
    fname_match = None
    mname_match = None
    dob_match = None
    for text in texts:
        if id_match is None:
            id_match = re.search(id_pattern, text.description)
        if lname_match is None:
            lname_match = re.search(lname_pattern, text.description)
        if fname_match is None:
            fname_match = re.search(fname_pattern, text.description)
        if mname_match is None:
            mname_match = re.search(mname_pattern, text.description)
        if dob_match is None:
            dob_match = re.search(dob_pattern, text.description)
        if id_match and lname_match and fname_match and mname_match and dob_match:
            break

    if id_match and fname_match and lname_match and dob_match:
        return {
            'id_number': id_match.group(1),
            'first_name': fname_match.group(1),
            'middle_name': mname_match.group(1),
            'last_name': lname_match.group(1),
            'dob': dob_match.group(1)}


def store_sql(extracted_data, is_same_person, similarity):
    # store extracted texts in database
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO philsys.philippine_national_id (id_number, first_name, middle_name, last_name, dob, face_match, match_percent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_number) DO NOTHING;
                ''',
                (
                    extracted_data['id_number'],
                    extracted_data['first_name'],
                    extracted_data['middle_name'],
                    extracted_data['last_name'],
                    extracted_data['dob'],
                    is_same_person,
                    similarity
                ))
            conn.commit()

        resp = make_response(jsonify({'status': 'success', 'data': extracted_data}))
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp

    except Exception as e:
        traceback.print_exc()
        resp = make_response(jsonify({'status': 'error', 'message': str(e)}))
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp


if __name__ == "__main__":
    app.run(debug=True)
