import re
import face_recognition
import numpy as np
import base64
import cv2
from .database import get_all_face_encodings

def validate_base64_image(base64_string):
    if not base64_string or not isinstance(base64_string, str): return False, ""
    data_url_pattern = r'^data:image\/(jpeg|png|webp|gif);base64,[A-Za-z0-9+/=]+'
    if base64_string.startswith('data:'):
        if not re.match(data_url_pattern, base64_string): return False, ""
        return True, base64_string.split(',', 1)[1]
    try:
        base64.b64decode(base64_string, validate=True)
        return True, base64_string
    except Exception: return False, ""

def decode_image_from_base64(base64_string):
    is_valid, clean_b64 = validate_base64_image(base64_string)
    if not is_valid: return None
    try:
        img_bytes = base64.b64decode(clean_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None: return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception: return None

def get_face_encoding(image):
    face_locations = face_recognition.face_locations(image)
    if len(face_locations) == 0: return None, "No face detected. Please ensure your face is clearly visible."
    if len(face_locations) > 1: return None, "Multiple faces detected. Please ensure only one face is in the frame."
    encodings = face_recognition.face_encodings(image, face_locations)
    if len(encodings) == 0: return None, "Could not encode face. Please try again."
    return encodings[0], "Face encoding successful!"

def encode_face_from_base64(base64_string):
    image = decode_image_from_base64(base64_string)
    if image is None: return None, "Invalid image data. Please try again."
    return get_face_encoding(image)

def match_face(base64_string, tolerance=0.45):
    image = decode_image_from_base64(base64_string)
    if image is None: return None, "Invalid image data."
    encoding, msg = get_face_encoding(image)
    if encoding is None: return None, msg
    all_students = get_all_face_encodings()
    if not all_students: return None, "No registered students found in the database."
    known_encodings = [s['encoding'] for s in all_students]
    distances = face_recognition.face_distance(known_encodings, encoding)
    if len(distances) == 0: return None, "No matches found."
    best_match_idx = np.argmin(distances)
    best_distance = distances[best_match_idx]
    if best_distance <= tolerance:
        matched = all_students[best_match_idx]
        confidence = round((1 - best_distance) * 100, 1)
        return {
            'id': matched['id'], 'name': matched['name'], 'reg_number': matched['reg_number'],
            'branch': matched['branch'], 'confidence': confidence
        }, f"Face matched with {confidence}% confidence!"
    else: return None, "Face not recognized. Please try again or register first."
