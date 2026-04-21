import urllib.request
import json

req = urllib.request.Request('http://127.0.0.1:7891/chat', method='POST')
req.add_header('Content-Type', 'application/json')
data = json.dumps({"message": "test", "contextType": "workspace", "workspacePath": "."}).encode('utf-8')

try:
    with urllib.request.urlopen(req, data=data) as response:
        response_text = response.read()
        print(f"Status: {response.status}")
        print(f"Response: {response_text.decode('utf-8')}")
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8')
    print(f"HTTPError: {e.code} {e.reason}")
    print(f"Error body: {error_body}")
except Exception as e:
    print(f"Exception: {e}")
