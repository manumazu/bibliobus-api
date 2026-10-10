#==============================================================================
# Copyright (C) 2026  Emmanuel Mazurier <contact@bibliob.us>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#==============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Union
from paddleocr import PaddleOCR
from dependencies import get_auth_device
from pathlib import Path
from config import settings
import tools
import cv2
import os

router = APIRouter(
    prefix="/ocr",
    tags=["OCR"],
    dependencies=[Depends(get_auth_device)],
    responses={404: {"description": "Not found"}},
)

ocr = PaddleOCR(
    #lang="fr",
    text_detection_model_name="PP-OCRv6_tiny_det",
    text_recognition_model_name="PP-OCRv6_tiny_rec",
    #PP-OCRv6_medium_det
    
    use_doc_orientation_classify=False, # Disables document orientation classification model via this parameter
    use_doc_unwarping=False, # Disables text image rectification model via this parameter
    use_textline_orientation=False, # Disables text line orientation classification model via this parameter

    # use_angle_cls=False,
    # enable_mkldnn=True,
    # cpu_threads=8,
    # det_limit_side_len=960,
) 

@router.post("/predict/{img_crop_name}")
async def predict_book_title(current_device: Annotated[str, Depends(get_auth_device)], img_crop_name: str, numshelf: int):
    """Get ocr for book image crop"""
    device = current_device.get('device')
    user = current_device.get('user')

    crop_dir = os.path.join(settings.app_upload_folder, 'users', str(user['id']), str(device['id']), str(numshelf), 'crop')
    img_crop_path = os.path.join(settings.app_root_path, crop_dir, img_crop_name)     
    
    crop_preprocessed = cv2.imread(img_crop_path)

    best_crop, best_angle, score, ocr_results = evaluate_rotation_confidence(img_crop_name, crop_preprocessed, ocr)
    
    output = False
    if len(ocr_results) > 1 :
        output = {'title': ocr_results}    
    return output


def evaluate_rotation_confidence(img_crop_name, crop_gray, ocr):
    """
    Test 4 orientations (0°, 90° CW, 180°, 90° CCW) pour trouver celle
    qui donne le meilleur score de confiance global avec EasyOCR.
    """
    rotations = [
        ("0", None),
        ("90_CW", cv2.ROTATE_90_CLOCKWISE),
        ("180", cv2.ROTATE_180),
        #("90_CCW", cv2.ROTATE_90_COUNTERCLOCKWISE)
    ]
    best_score = -1.0
    best_angle = "0"
    best_image = crop_gray
    best_ocr_results = []

    for angle_label, cv_rotate_code in rotations:
        if cv_rotate_code is not None:
            rotated = cv2.rotate(crop_gray, cv_rotate_code)
        else:
            rotated = crop_gray.copy()

        # Lecture OCR sur fichier tmp
        crop_filename = os.path.join("/tmp/", f"{img_crop_name}_{angle_label}.jpg")
        cv2.imwrite(crop_filename, rotated)
        results = ocr.predict(crop_filename)
        os.remove(crop_filename)

        # Calcul d'un score de confiance pondéré par la longueur des mots détectés
        total_conf = 0.0
        total_len = 0
        valid_words = 0

        for res in results:
            
            # weight score confidence with text length
            score = 0
            text = ''
            for i, conf in enumerate(res['rec_scores']):
                text_tmp = res['rec_texts'][i].strip()
                text_len = len(text_tmp)
                if conf > 0.9 and text_len > 1:
                    score += conf * text_len
                    # remove strings with numbers
                    if not text_tmp.isnumeric():
                        text += f"{text_tmp} "
                else:
                    score -= conf
                #logger.info(f"----eval : score: {score}, conf: {conf}")

            #text = ' '.join(res['rec_texts'])
            clean_text = text.strip()  
            
            #print(f"--test: score: {score}, text: {clean_text}, res: {res['rec_texts']}")
            
        if score > best_score:
            best_score = score
            best_angle = angle_label
            best_image = rotated
            best_ocr_results = clean_text

    return best_image, best_angle, best_score, best_ocr_results