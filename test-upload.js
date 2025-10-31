#!/usr/bin/env node

/**
 * Google Gemini Files API 上传测试脚本
 * 用法: node test-upload.js <API_KEY> <FILE_PATH>
 */

const fs = require('fs');
const https = require('https');

const apiKey = process.argv[2];
const filePath = process.argv[3];

if (!apiKey || !filePath) {
  console.error('用法: node test-upload.js <API_KEY> <FILE_PATH>');
  console.error('示例: node test-upload.js AIza... /path/to/video.mp4');
  process.exit(1);
}

if (!fs.existsSync(filePath)) {
  console.error('❌ 文件不存在:', filePath);
  process.exit(1);
}

const fileData = fs.readFileSync(filePath);
const mimeType = filePath.endsWith('.mp4') ? 'video/mp4' : 
                 filePath.endsWith('.jpg') || filePath.endsWith('.jpeg') ? 'image/jpeg' :
                 filePath.endsWith('.png') ? 'image/png' : 'application/octet-stream';

console.log('\n📤 开始测试文件上传...');
console.log('文件路径:', filePath);
console.log('文件大小:', fileData.length, 'bytes');
console.log('MIME 类型:', mimeType);
console.log('API Key:', apiKey.substring(0, 10) + '...');
console.log('\n--- 直接调用 Google API ---\n');

const options = {
  hostname: 'generativelanguage.googleapis.com',
  port: 443,
  path: '/upload/v1beta/files?upload_type=media',
  method: 'POST',
  headers: {
    'Content-Type': mimeType,
    'Content-Length': fileData.length,
    'X-Goog-Api-Key': apiKey
  }
};

const req = https.request(options, (res) => {
  console.log('✅ 响应状态码:', res.statusCode);
  console.log('📋 响应头:');
  Object.keys(res.headers).forEach(key => {
    console.log(`  ${key}: ${res.headers[key]}`);
  });
  console.log('\n📦 响应体:');

  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    console.log(data);
    
    try {
      const json = JSON.parse(data);
      console.log('\n📊 解析后的 JSON:');
      console.log(JSON.stringify(json, null, 2));
      
      if (json.file) {
        console.log('\n✅ 文件信息:');
        console.log('  文件名:', json.file.name);
        console.log('  文件 ID:', json.file.name ? json.file.name.split('/')[1] : 'N/A');
        console.log('  URI:', json.file.uri);
        console.log('  状态:', json.file.state);
      }
    } catch (e) {
      console.log('⚠️  无法解析 JSON:', e.message);
    }
  });
});

req.on('error', (e) => {
  console.error('❌ 请求失败:', e.message);
});

req.write(fileData);
req.end();


