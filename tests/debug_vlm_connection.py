import asyncio
import os
import sys
import base64
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from src.config import Config

def create_dummy_image_b64():
    """Create a 64x64 red PNG image in base64"""
    # 64x64 red PNG (using a slightly larger valid PNG structure)
    import io
    try:
        from PIL import Image
        img = Image.new('RGB', (64, 64), color='red')
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except ImportError:
        # Fallback to a hardcoded 2x2 red pixel PNG if PIL is not available
        # This is a valid 2x2 red PNG hex string
        png_hex = (
            "89504e470d0a1a0a0000000d4948445200000002000000020802000000fdd49a730000000c"
            "4944415408d763f8cfc000000301010018dd8db00000000049454e44ae426082"
        )
        return base64.b64encode(bytes.fromhex(png_hex)).decode('utf-8')

async def test_vlm():
    load_dotenv()
    
    print("Loading config...")
    try:
        config = Config(config_file_path='my_config.yaml')
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    vlm_model_name = os.getenv("VLM_MODEL_NAME")
    if not vlm_model_name:
        print("Error: VLM_MODEL_NAME environment variable not set")
        return
        
    print(f"VLM Model Name: {vlm_model_name}")
    
    if vlm_model_name not in config.llm_dict:
        print(f"Error: VLM model '{vlm_model_name}' not found in config.llm_dict")
        print(f"Available models: {list(config.llm_dict.keys())}")
        return

    vlm = config.llm_dict[vlm_model_name]
    print("VLM instance retrieved.")
    print(f"Base URL: {vlm.client.base_url}")
    masked_key = vlm.client.api_key[:4] + "****" + vlm.client.api_key[-4:] if vlm.client.api_key else "None"
    print(f"API Key: {masked_key}")

    image_b64 = create_dummy_image_b64()
    
    messages = [
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": "What color is this image? Please answer in one word."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]
        }
    ]

    print("Sending request to VLM...")
    try:
        response = await vlm.generate(messages=messages)
        print("\n--- VLM Response ---")
        print(response)
        print("--------------------")
        
        if "red" in str(response).lower():
            print("\nSUCCESS: VLM correctly identified the color.")
        else:
            print("\nWARNING: VLM response did not contain 'red'. Check the output manually.")
            
    except Exception as e:
        print(f"\nERROR: VLM request failed: {e}")
    finally:
        await config.close()

if __name__ == "__main__":
    asyncio.run(test_vlm())
