#!/usr/bin/env python3
"""
Google Gemini Files API 上传测试脚本
用法: python test-upload.py <API_KEY> <FILE_PATH>
"""

import sys
import json
import requests

if len(sys.argv) != 3:
    print("用法: python test-upload.py <API_KEY> <FILE_PATH>")
    print("示例: python test-upload.py AIza... /path/to/video.mp4")
    sys.exit(1)

api_key = sys.argv[1]
file_path = sys.argv[2]

# 检测 MIME 类型
if file_path.endswith('.mp4'):
    mime_type = 'video/mp4'
elif file_path.endswith(('.jpg', '.jpeg')):
    mime_type = 'image/jpeg'
elif file_path.endswith('.png'):
    mime_type = 'image/png'
else:
    mime_type = 'application/octet-stream'

print('\n📤 开始测试文件上传...')
print(f'文件路径: {file_path}')
print(f'MIME 类型: {mime_type}')
print(f'API Key: {api_key[:10]}...')
print('\n--- 直接调用 Google API ---\n')

try:
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    print(f'文件大小: {len(file_data)} bytes')
    
    url = 'https://generativelanguage.googleapis.com/upload/v1beta/files?upload_type=media'
    headers = {
        'Content-Type': mime_type,
        'X-Goog-Api-Key': api_key
    }
    
    response = requests.post(url, headers=headers, data=file_data)
    
    print(f'✅ 响应状态码: {response.status_code}')
    print('\n📋 响应头:')
    for key, value in response.headers.items():
        print(f'  {key}: {value}')
    
    print('\n📦 响应体:')
    print(response.text)
    
    if response.status_code == 200:
        try:
            data = response.json()
            print('\n📊 解析后的 JSON:')
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if 'file' in data:
                print('\n✅ 文件信息:')
                print(f"  文件名: {data['file'].get('name', 'N/A')}")
                file_name = data['file'].get('name', '')
                file_id = file_name.split('/')[-1] if file_name else 'N/A'
                print(f"  文件 ID: {file_id}")
                print(f"  URI: {data['file'].get('uri', 'N/A')}")
                print(f"  状态: {data['file'].get('state', 'N/A')}")
        except json.JSONDecodeError as e:
            print(f'⚠️  无法解析 JSON: {e}')
    else:
        print(f'\n❌ 上传失败: {response.status_code}')

except FileNotFoundError:
    print(f'❌ 文件不存在: {file_path}')
    sys.exit(1)
except Exception as e:
    print(f'❌ 错误: {e}')
    sys.exit(1)


