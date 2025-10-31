#!/usr/bin/env python3
"""
对比代理服务器和 Google 原始 API 的响应
用法: python test-proxy-compare.py <API_KEY> <FILE_PATH>
"""

import json
import sys
import urllib.error
import urllib.request

if len(sys.argv) != 3:
    print("用法: python test-proxy-compare.py <API_KEY> <FILE_PATH>")
    print("示例: python test-proxy-compare.py AIza... /path/to/video.mp4")
    sys.exit(1)

api_key = sys.argv[1]
file_path = sys.argv[2]

# 检测 MIME 类型
if file_path.endswith(".mp4"):
    mime_type = "video/mp4"
elif file_path.endswith((".jpg", ".jpeg")):
    mime_type = "image/jpeg"
elif file_path.endswith(".png"):
    mime_type = "image/png"
else:
    mime_type = "application/octet-stream"

print("\n" + "=" * 80)
print("📤 Google Gemini Files API 上传对比测试")
print("=" * 80)
print(f"文件路径: {file_path}")
print(f"MIME 类型: {mime_type}")
print(f"API Key: {api_key[:10]}...")
print("=" * 80 + "\n")

try:
    with open(file_path, "rb") as f:
        file_data = f.read()

    print(f"✅ 文件读取成功: {len(file_data)} bytes\n")

    # 测试配置
    tests = [
        {
            "name": "🌐 Google 原始 API",
            "url": "https://generativelanguage.googleapis.com/upload/v1beta/files?upload_type=media",
            "headers": {"Content-Type": mime_type, "X-Goog-Api-Key": api_key},
        },
        {
            "name": "🔄 通过代理服务器 (proxy.cms4.cc)",
            "url": "https://proxy.cms4.cc/generativelanguage/upload/v1beta/files?upload_type=media",
            "headers": {"Content-Type": mime_type, "X-Goog-Api-Key": api_key},
        },
    ]

    results = []

    for test in tests:
        print("\n" + "-" * 80)
        print(f"{test['name']}")
        print("-" * 80)
        print(f"📍 URL: {test['url']}")
        print(f"📋 Headers: {test['headers']}")
        print("\n发送请求...")

        try:
            # 使用 urllib 发送请求
            req = urllib.request.Request(
                test["url"], data=file_data, headers=test["headers"], method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.status
                response_headers = dict(response.headers)
                response_body = response.read().decode("utf-8")

                print(f"✅ 响应状态码: {status_code}")
                print(f"📏 响应体长度: {len(response_body)} bytes")

                print("\n📋 响应头:")
                for key, value in response_headers.items():
                    print(f"  {key}: {value}")

                print("\n📦 响应体内容:")
                print(response_body)

                result = {
                    "name": test["name"],
                    "status": status_code,
                    "headers": response_headers,
                    "body": response_body,
                    "body_length": len(response_body),
                }

                if status_code == 200:
                    try:
                        data = json.loads(response_body)
                        print("\n📊 解析后的 JSON:")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        result["json"] = data

                        if "file" in data:
                            print("\n✅ 文件信息:")
                            print(f"  文件名: {data['file'].get('name', 'N/A')}")
                            file_name = data["file"].get("name", "")
                            file_id = file_name.split("/")[-1] if file_name else "N/A"
                            print(f"  文件 ID: {file_id}")
                            print(f"  URI: {data['file'].get('uri', 'N/A')}")
                            print(f"  状态: {data['file'].get('state', 'N/A')}")
                            result["file_id"] = file_id
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️  无法解析 JSON: {e}")
                        result["json_error"] = str(e)
                else:
                    print("\n❌ 上传失败")

                results.append(result)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else "No error body"
            print(f"\n❌ HTTP 错误: {e.code} {e.reason}")
            print(f"错误响应: {error_body}")
            results.append(
                {
                    "name": test["name"],
                    "status": e.code,
                    "error": f"{e.code} {e.reason}",
                    "body": error_body,
                }
            )
        except urllib.error.URLError as e:
            print(f"\n❌ 请求失败: {e.reason}")
            results.append({"name": test["name"], "error": str(e.reason)})
        except Exception as e:
            print(f"\n❌ 未知错误: {e}")
            results.append({"name": test["name"], "error": str(e)})

    # 对比结果
    print("\n\n" + "=" * 80)
    print("📊 对比结果")
    print("=" * 80)

    if len(results) == 2:
        r1, r2 = results

        print(f"\n1️⃣  {r1.get('name', 'Test 1')}")
        print(f"   状态码: {r1.get('status', 'N/A')}")
        print(f"   响应长度: {r1.get('body_length', 'N/A')} bytes")
        print(f"   文件 ID: {r1.get('file_id', 'N/A')}")

        print(f"\n2️⃣  {r2.get('name', 'Test 2')}")
        print(f"   状态码: {r2.get('status', 'N/A')}")
        print(f"   响应长度: {r2.get('body_length', 'N/A')} bytes")
        print(f"   文件 ID: {r2.get('file_id', 'N/A')}")

        # 差异分析
        print("\n🔍 差异分析:")

        if r1.get("status") == r2.get("status"):
            print("   ✅ 状态码一致")
        else:
            print(f"   ❌ 状态码不同: {r1.get('status')} vs {r2.get('status')}")

        if r1.get("body_length") == r2.get("body_length"):
            print("   ✅ 响应长度一致")
        else:
            print(
                f"   ⚠️  响应长度不同: {r1.get('body_length')} vs {r2.get('body_length')} bytes"
            )

        if r1.get("file_id") == r2.get("file_id"):
            print("   ✅ 文件 ID 一致")
        else:
            print(f"   ⚠️  文件 ID 不同: {r1.get('file_id')} vs {r2.get('file_id')}")

        # Content-Type 对比
        ct1 = r1.get("headers", {}).get("content-type", "N/A")
        ct2 = r2.get("headers", {}).get("content-type", "N/A")
        if ct1 == ct2:
            print(f"   ✅ Content-Type 一致: {ct1}")
        else:
            print("   ⚠️  Content-Type 不同:")
            print(f"      原始: {ct1}")
            print(f"      代理: {ct2}")

    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80 + "\n")

except FileNotFoundError:
    print(f"❌ 文件不存在: {file_path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
