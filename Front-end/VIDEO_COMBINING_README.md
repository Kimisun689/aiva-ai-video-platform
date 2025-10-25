# Video Combining Feature

## Overview
The video combining feature allows you to merge all AI-generated video shots into a single video file using `ffmpeg.js` (WebAssembly) in the browser.

## Browser Security Requirements

### SharedArrayBuffer Issue
The `SharedArrayBuffer` error occurs because modern browsers require specific HTTP headers for security reasons when using WebAssembly features like `ffmpeg.js`.

### Required HTTP Headers
```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

## Solutions

### Option 1: Install Node.js and use http-server (Recommended)
1. Install Node.js from https://nodejs.org/
2. Run the startup script:
   ```bash
   cd Front-end
   ./start_server.sh
   ```

### Option 2: Use Python server (Limited functionality)
```bash
cd Front-end
python3 -m http.server 8080
```
**Note**: This will show the manual download option instead of automatic video combining.

### Option 3: Manual Download
If video combining fails, the system will automatically show a manual download option where you can:
1. Download each video shot individually
2. Use external video editing software to combine them
3. Use online video combiners

## Troubleshooting

### Error: "SharedArrayBuffer is not defined"
- **Cause**: Missing required HTTP headers
- **Solution**: Use the startup script or install Node.js

### Error: "FFmpeg library not loaded"
- **Cause**: Network issues or CDN problems
- **Solution**: Check internet connection or try the manual download option

### Error: "Video combination failed"
- **Cause**: Various technical issues
- **Solution**: Use the manual download option as fallback

## Manual Download Instructions
If automatic combining fails, you can:
1. Download each video URL individually
2. Use video editing software like:
   - FFmpeg (command line)
   - Adobe Premiere
   - DaVinci Resolve
   - Online tools like:
     - https://www.onlinevideoconverter.com/
     - https://www.youcompress.com/
     - https://www.media.io/

## Technical Details
- Video format: MP4 (H.264)
- Duration per shot: 5 seconds
- Total duration: Number of shots × 5 seconds
- Output: Single MP4 file with all shots concatenated 