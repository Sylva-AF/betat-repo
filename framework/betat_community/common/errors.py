"""The standard API error shape (BLUEPRINT §0 Conventions): every error
response is `{"error": {"code": "<machine_code>", "message": "<human text>"}}`
with the matching HTTP status. One helper so every app's api/views.py
renders errors identically.
"""
from rest_framework.response import Response


def error_response(code, message, status):
    return Response({'error': {'code': code, 'message': message}}, status=status)
