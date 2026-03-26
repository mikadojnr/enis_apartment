from flask_login import current_user
import requests
from flask import current_app, jsonify, request
from app.verification import verification_bp
from app import db

from app.models import VerifiedID

@verification_bp.route('', methods=['POST'])
def verify_id():
    """Reusable ID Verification using IDAnalyzer / DocuPass"""
    if not request.is_json:
        return jsonify({"success": False, "message": "JSON required"}), 400

    data = request.get_json()
    id_type = data.get('id_type')
    document_url = data.get('document_url')      # uploaded file URL
    selfie_url = data.get('selfie_url')          # optional for face match

    if not document_url:
        return jsonify({"success": False, "message": "Document is required"}), 400

    try:
        # === IDAnalyzer API Call (replace with your actual key) ===
        api_key = current_app.config.get('IDANALYZER_API_KEY')
        if not api_key:
            return jsonify({"success": False, "message": "Verification service not configured"}), 500

        payload = {
            "document": document_url,
            "selfie": selfie_url,
            "id_type": id_type.upper(),   # NIN, PASSPORT, DRIVERS_LICENSE
            "country": "NG",
            "face_match": True if selfie_url else False
        }

        response = requests.post(
            "https://api.idanalyzer.com/v2/verify",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"}
        )

        result = response.json()

        if result.get("success") and result.get("verified") is True:
            # Store verification
            verified_id = VerifiedID(
                user_id=current_user.id if current_user.is_authenticated else None,
                email=data.get('email'),
                id_type=id_type,
                id_number=result.get('document_number'),
                full_name=result.get('full_name'),
                date_of_birth=result.get('dob'),
                verification_id=result.get('transaction_id'),
                document_url=document_url,
                selfie_url=selfie_url
            )
            db.session.add(verified_id)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "ID verified successfully",
                "verified_id_id": verified_id.id,
                "full_name": result.get('full_name')
            })
        else:
            return jsonify({
                "success": False,
                "message": result.get("message", "ID verification failed")
            }), 400

    except Exception as e:
        current_app.logger.error(f"ID Verification error: {e}")
        return jsonify({"success": False, "message": "Verification service error"}), 500