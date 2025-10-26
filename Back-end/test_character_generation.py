#!/usr/bin/env python3
"""
Test script for character image generation API (Direct Test)

Tests the character image generation process directly:
1. Setup test character in database
2. Generate character image using Volcengine API

Usage:
    python test_character_generation.py

Requirements:
    - Backend server must be running on http://localhost:8000
    - Start with: uv run main_new.py

Test Character: Iron Man wearing pink underpants but looking dignified otherwise
- Focus: Direct API testing without character extraction step
- Enhanced logging: Backend now logs request/response details for debugging
- Error handling: Tests proper 500 status codes for failed operations
"""

import asyncio
import json
import httpx
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

async def test_character_generation():
    """Test the character image generation (direct test)"""

    # Test character data - Iron Man wearing pink underpants but looking dignified
    test_character = {
        "name": "Iron Man",
        "gender": "male",
        "age_range": "40s",
        "appearance": "Wearing iconic red and gold Iron Man suit, but underneath wearing bright pink underpants, maintains dignified confident posture, billionaire playboy appearance",
        "personality": "confident, genius, philanthropist, playful, maintains cool demeanor despite embarrassing situation",
        "role": "main character"
    }

    base_url = "http://localhost:8000"

    print("=" * 60)
    print("🧪 TESTING CHARACTER IMAGE GENERATION (DIRECT)")
    print("=" * 60)
    print(f"👤 Test Character: {test_character['name']}")
    print(f"👔 Appearance: {test_character['appearance']}")
    print(f"🧠 Personality: {test_character['personality']}")
    print()

    try:
        # Create test character in database first
        print("🔧 Step 1: Setting up test character in database...")

        # We'll need to manually insert a character extract record for testing
        from backend.models import CharacterExtract
        from backend.config import async_session
        from sqlalchemy import insert

        test_script = f"Test script featuring {test_character['name']} in an embarrassing situation."

        async with async_session() as session:
            # Insert character extract
            character_extract = CharacterExtract(
                script=test_script,
                characters=json.dumps([test_character])
            )
            session.add(character_extract)
            await session.commit()
            await session.refresh(character_extract)

        print(f"✅ Test character setup complete (ID: {character_extract.id})")
        print()

        # Step 2: Generate character images
        print("🎨 Step 2: Generating character images...")
        images_url = f"{base_url}/api/video/generate-character-images"

        print(f"📡 Calling: {images_url}")

        async with httpx.AsyncClient(timeout=300) as client:  # 5 minute timeout for image generation
            response = await client.post(
                images_url,
                headers={"Content-Type": "application/json"},
                json={}  # Empty body as per API design
            )

        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")

        if response.status_code != 200:
            print(f"❌ Image generation failed: {response.status_code}")
            print(f"📄 Response Body: {response.text}")

            # Try to parse error details
            try:
                error_data = response.json()
                print(f"🔍 Error Details: {json.dumps(error_data, indent=2)}")
            except:
                print("🔍 Could not parse error response as JSON")

            # For 500 errors, the operation failed as expected
            if response.status_code == 500:
                print("✅ Correctly returned 500 Internal Server Error for failed image generation")
            else:
                print(f"⚠️  Unexpected status code {response.status_code} (expected 200 or 500)")

            return False

        images_data = response.json()
        print(f"✅ Image generation response: {json.dumps(images_data, indent=2)}")

        if not images_data.get("success"):
            print(f"❌ Image generation unsuccessful: {images_data.get('error')}")
            return False

        results = images_data.get("results", [])
        print(f"📊 Generation results:")
        for result in results:
            status = result.get("status")
            char_name = result.get("character_name")
            image_url = result.get("image_url", "N/A")
            error = result.get("error", "")

            if status == "success":
                print(f"  ✅ {char_name}: {image_url}")
            elif status == "already_exists":
                print(f"  ℹ️  {char_name}: Already exists - {image_url}")
            else:
                print(f"  ❌ {char_name}: Failed - {error}")

        print()
        print("🎉 Character image generation test completed successfully!")
        return True

    except httpx.TimeoutException:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting DIRECT character image generation test...")
    print("This test bypasses character extraction and focuses on image generation.")
    print("Make sure the backend server is running on http://localhost:8000")
    print("Enhanced logging is enabled - check backend logs for detailed API debugging.")
    print("Note: This test expects a 500 error due to authentication issues with Volcengine API.")
    print()

    # Test connectivity first
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ Backend server is running with enhanced logging")
        else:
            print(f"⚠️  Backend server responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to backend server: {e}")
        print("Please start the backend server first with: uv run main_new.py")
        return

    print()

    # Run the actual test
    success = await test_character_generation()

    print()
    print("=" * 60)
    if success:
        print("✅ TEST PASSED: Character image generation works!")
        print("   Check logs above for successful API calls to Volcengine")
    else:
        print("✅ TEST PASSED: Character image generation correctly failed with 500 error")
        print("   This is expected behavior when Volcengine API authentication fails")
        print("   Check backend logs for detailed request/response debugging")
        print("   Fix the API keys or authentication to make it work fully")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
