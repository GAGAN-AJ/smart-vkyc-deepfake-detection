import cv2
import pytesseract
from PIL import Image
from lxml import etree
from rapidfuzz import fuzz
import re
import shutil
import logging
import os

logging.basicConfig(level=logging.INFO)


class DocumentVerifier:
    def __init__(self, image_path):
        if not image_path:
            raise ValueError("Image path cannot be empty.")
        self.image_path = image_path
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"File does not exist at path: {self.image_path}")
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise ValueError(f"OpenCV could not read image at {self.image_path}.")

    def decode_qr_code(self):
        try:
            detector = cv2.QRCodeDetector()
            data, points, _ = detector.detectAndDecode(self.image)
            if not data:
                logging.warning("No QR code found.")
                return None
            xml_start = data.find("<?xml")
            if xml_start == -1:
                return {"raw_data": data}
            xml_data = data[xml_start:]
            try:
                root = etree.fromstring(xml_data.encode("utf-8"))
                return {
                    "name": root.get("name"),
                    "dob": root.get("dob"),
                    "gender": root.get("gender"),
                    "pincode": root.get("pc"),
                }
            except etree.XMLSyntaxError:
                return {"raw_data": data}
        except Exception as e:
            logging.error(f"QR decode error: {e}")
            return None

    def extract_text_with_ocr(self):
        try:
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            pil_img = Image.fromarray(gray)
            return pytesseract.image_to_string(pil_img, lang="eng").lower()
        except Exception as e:
            logging.error(f"OCR error: {e}")
            return ""

    def verify_document(self):
        qr_info = self.decode_qr_code()
        if not qr_info:
            return {"status": "REJECTED", "reason": "No QR code found."}
        ocr_text = self.extract_text_with_ocr()
        if not ocr_text:
            return {"status": "FLAGGED", "reason": "No text extracted."}
        ocr_text = " ".join(ocr_text.split())
        mismatches = []
        if qr_info.get("name"):
            score = fuzz.partial_ratio(qr_info["name"].lower(), ocr_text)
            if score < 80:
                mismatches.append(f"Name mismatch (Score: {score})")
        if qr_info.get("dob"):
            pattern = qr_info["dob"].replace("-", "[/-]").replace("/", "[/-]")
            if not re.search(pattern, ocr_text):
                mismatches.append("DOB mismatch")
        if mismatches:
            return {
                "status": "FLAGGED",
                "reason": "Mismatch.",
                "mismatched_fields": mismatches,
                "qr_data": qr_info,
            }
        return {"status": "VERIFIED", "reason": "OK.", "qr_data": qr_info}