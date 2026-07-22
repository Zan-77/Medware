import os
import sys
import django
import json

# Ensure project root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
from django.conf import settings

c = Client()

print('BASE URL: /api')

# Register
reg_data = {
    'username': 'apitest',
    'email': 'apitest@example.com',
    'password': 'testpass',
    'role': 'CUSTOMER',
}
print('\nPOST /api/auth/register/')
output_path = os.path.join(BASE_DIR, 'scripts', 'smoke_result.txt')
with open(output_path, 'w', encoding='utf-8') as out:
    try:
        resp = c.post('/api/auth/register/', json.dumps(reg_data), content_type='application/json')
        out.write(f'REGISTER STATUS: {resp.status_code}\n')
        out.write((resp.content.decode()[:2000] or '') + '\n')
    except Exception:
        import traceback
        out.write('REGISTER EXCEPTION\n')
        out.write(traceback.format_exc())

    # Try token obtain
    out.write('\nPOST /api/auth/token/\n')
    try:
        resp2 = c.post('/api/auth/token/', json.dumps({'username':'apitest','password':'testpass'}), content_type='application/json')
        out.write(f'TOKEN STATUS: {resp2.status_code}\n')
        out.write((resp2.content.decode()[:2000] or '') + '\n')
    except Exception:
        import traceback
        out.write('TOKEN EXCEPTION\n')
        out.write(traceback.format_exc())

    # Get current user using session auth (should not be authenticated)
    out.write('\nGET /api/users/me/ (before login)\n')
    try:
        resp3 = c.get('/api/users/me/')
        out.write(f'ME STATUS: {resp3.status_code}\n')
        out.write((resp3.content.decode()[:2000] or '') + '\n')
    except Exception:
        import traceback
        out.write(traceback.format_exc())

    # If token present, try passing Authorization header for access
    try:
        data = resp2.json()
        access = data.get('access')
        if access:
            out.write('\nGET /api/users/me/ with JWT\n')
            resp4 = c.get('/api/users/me/', HTTP_AUTHORIZATION=f'Bearer {access}')
            out.write(f'ME WITH JWT STATUS: {resp4.status_code}\n')
            out.write((resp4.content.decode()[:2000] or '') + '\n')
    except Exception as e:
        out.write('Token step skipped or failed: ' + repr(e) + '\n')
