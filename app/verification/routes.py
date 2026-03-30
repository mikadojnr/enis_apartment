import os

from flask_login import current_user
import idanalyzer
import requests
from flask import current_app, jsonify, request
from werkzeug.utils import secure_filename
from app.verification import verification_bp
from app import db

from app.models import VerifiedID

@verification_bp.route('', methods=['POST'])
def verify_id():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400

    file = request.files['file']
    id_type = request.form.get('id_type', 'nin')
    email = request.form.get('email', '').strip().lower()

    if not file or file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400

    try:
        # Initialize SDK with Server API Key
        coreapi = idanalyzer.CoreAPI(
            current_app.config.get('IDANALYZER_API_KEY'),
            current_app.config.get('IDANALYZER_REGION', 'US')
        )
        coreapi.throw_api_exception(True)
        coreapi.enable_authentication(True, 'quick')

        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)

        # === IMPORTANT: Pass local file path directly (SDK supports this) ===
        response = coreapi.scan(document_primary=temp_path)

        # Optional cleanup
        # os.remove(temp_path)

        if response.get('result'):
            data = response['result']

            verified = VerifiedID(
                user_id=current_user.id if current_user.is_authenticated else None,
                email=email or None,
                id_type=id_type,
                id_number=data.get('documentNumber') or data.get('idNumber'),
                full_name=f"{data.get('firstName','')} {data.get('lastName','')}".strip(),
                verification_id=response.get('transactionId'),
                document_url=f"/uploads/ids/{filename}",   # you can move file later
                is_verified=True
            )
            db.session.add(verified)
            db.session.commit()

            return jsonify({
                "success": True,
                "verified_id_id": verified.id,
                "full_name": verified.full_name,
                "message": "ID verified successfully"
            })

        return jsonify({"success": False, "message": "Could not read the document"}), 400

    except idanalyzer.APIError as e:
        details = e.args[0]
        return jsonify({
            "success": False,
            "message": details.get("message", "API Error")
        }), 400

    except Exception as e:
        current_app.logger.error(f"Verification error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Internal verification error"}), 500
    

@verification_bp.route('/check-verified-email', methods=['GET'])
def check_verified_email():
    """Check if a guest email has a previously verified ID"""
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({"verified": False}), 200

    verified = VerifiedID.query.filter_by(email=email, is_verified=True).first()

    if verified:
        return jsonify({
            "verified": True,
            "verified_id_id": verified.id,
            "id_type": verified.id_type,
            "full_name": verified.full_name
        })
    else:
        return jsonify({"verified": False})