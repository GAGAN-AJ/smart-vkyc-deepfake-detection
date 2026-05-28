import cv2
import numpy as np
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

    def _try_decode(self, img):
        """Try both single and multi QR detection on a given image."""
        detector = cv2.QRCodeDetector()
        # Try multi first (better for dense codes)
        try:
            ok, decoded_info, points, _ = detector.detectAndDecodeMulti(img)
            if ok:
                for data in decoded_info:
                    if data:
                        return data
        except Exception:
            pass
        # Fallback to single
        try:
            data, points, _ = detector.detectAndDecode(img)
            if data:
                return data
        except Exception:
            pass
        return None

    def decode_qr_code(self):
        try:
            # Attempt 1: original image
            data = self._try_decode(self.image)

            # Attempt 2: grayscale
            if not data:
                gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
                data = self._try_decode(gray)

            # Attempt 3: upscaled versions (helps with small/dense QR)
            if not data:
                for scale in [1.5, 2.0, 3.0]:
                    resized = cv2.resize(self.image, None, fx=scale, fy=scale,
                                         interpolation=cv2.INTER_CUBIC)
                    data = self._try_decode(resized)
                    if data:
                        break

            # Attempt 4: sharpened grayscale
            if not data:
                gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
                sharpen_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                sharpened = cv2.filter2D(gray, -1, sharpen_kernel)
                data = self._try_decode(sharpened)

            # Attempt 5: thresholded
            if not data:
                gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                data = self._try_decode(thresh)

            if not data:
                logging.warning("No QR code found after all preprocessing attempts.")
                return None

            logging.info("QR code detected successfully.")
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