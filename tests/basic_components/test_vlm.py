import os
import sys
import base64
import io
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def create_dummy_image_b64():
    """Create a 64x64 red PNG image in base64"""
    try:
        from PIL import Image
        img = Image.new('RGB', (64, 64), color='red')
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except ImportError:
        # Fallback 2x2 red pixel
        png_hex = "89504e470d0a1a0a0000000d4948445200000002000000020802000000fdd49a730000000c4944415408d763f8cfc000000301010018dd8db00000000049454e44ae426082"
        return base64.b64encode(bytes.fromhex(png_hex)).decode('utf-8')

def test_vlm_completion():
    from openai import OpenAI
    
    # 确保有 base_url 和 model_name
    base_url = os.getenv("VLM_BASE_URL")
    model_name = os.getenv("VLM_MODEL_NAME")
    api_key = os.getenv("VLM_API_KEY")
    
    if not base_url or not model_name or not api_key:
        print("Skipping VLM test: VLM_BASE_URL, VLM_MODEL_NAME or VLM_API_KEY not set")
        return

    print(f"Testing VLM with model: {model_name}")
    vlm = OpenAI(api_key=api_key, base_url=base_url)
    
    image = create_dummy_image_b64()
    
    try:
        critic_response = vlm.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": "What color is this? Answer in one word."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}}
                ]}
            ],
            max_tokens=10
        )
        content = critic_response.choices[0].message.content
        print(f"VLM Response: {content}")
        if content:
            print("VLM Test PASSED")
        else:
            print("VLM Test FAILED: No content")
            
    except Exception as e:
        print(f"VLM API call failed: {str(e)}")

if __name__ == "__main__":
    test_vlm_completion()

