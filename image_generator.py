"""
Google Genai API (Gemini 2.0 Flash) を使用した画像生成モジュール
参照画像（背景・トレーナー）を活用して画像を生成
"""

import os
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types


def generate_image_with_gemini(
    prompt: str,
    reference_images: List[Dict[str, Any]],
    aspect_ratio: str = "1:1",
    resolution: str = "2K",
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Google Genai API (Gemini 2.0 Flash) を使用して画像を生成
    参照画像対応・高画質

    Args:
        prompt: 画像生成プロンプト（英語）
        reference_images: 参照画像のリスト
            各要素は {"path": Path, "type": "background"|"trainer", "description": str}
        aspect_ratio: アスペクト比 (例: "1:1", "16:9")
        resolution: 解像度 ("1K", "2K", "4K")
        output_dir: 出力ディレクトリ（Noneの場合はデフォルト）

    Returns:
        Dict: {
            "success": bool,
            "image_path": Path (成功時),
            "text_response": str,
            "error": str (失敗時)
        }
    """

    # API設定
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"success": False, "error": "GEMINI_API_KEY が設定されていません"}

    # 出力ディレクトリ設定
    if output_dir is None:
        output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    try:
        # クライアント初期化
        client = genai.Client(api_key=api_key)

        # コンテンツを構築
        contents = []

        # 参照画像の説明付きプロンプトを構築
        image_instructions = []

        # 背景画像とトレーナー画像を分類
        bg_images = [img for img in reference_images if img["type"] == "background"]
        trainer_images = [img for img in reference_images if img["type"] in ["trainer", "trainer_face"]]

        if bg_images:
            image_instructions.append(
                "【背景固定 - 絶対厳守】\n"
                "CRITICAL BACKGROUND INSTRUCTION: The provided background image shows the EXACT room/space to use. "
                "You MUST preserve ALL elements EXACTLY as they appear:\n"
                "- DO NOT move, add, remove, or modify ANY furniture (desks, chairs, equipment, shelves)\n"
                "- DO NOT change the wall colors, flooring, or architectural features\n"
                "- DO NOT alter the lighting setup or window positions\n"
                "- DO NOT rearrange or reposition ANY objects in the room\n"
                "- ONLY add/place people into this UNCHANGED environment\n"
                "The background must be 100% identical to the reference image - only human subjects are new."
            )

        if trainer_images:
            image_instructions.append(
                "【顔の完全再現 - 最重要】\n"
                "ABSOLUTE REQUIREMENT FOR FACE REPRODUCTION:\n"
                "Multiple reference photos of the trainer are provided showing different angles and expressions.\n"
                "You MUST faithfully reproduce this person's face with EXACT accuracy:\n"
                "- EXACT face shape, jawline, and bone structure\n"
                "- EXACT eye shape, eye size, eye spacing, and eyebrow shape\n"
                "- EXACT nose shape, size, and bridge\n"
                "- EXACT mouth shape and lip thickness\n"
                "- EXACT skin tone and any distinguishing features\n"
                "- EXACT hairstyle, hair color, and hairline\n"
                "The generated face must be IMMEDIATELY RECOGNIZABLE as the same person from the reference photos.\n"
                "The POSE and BODY POSITION can differ from reference photos - only the FACE must match exactly.\n"
                "This is a real person whose likeness must be preserved - do not generalize or stylize the facial features."
            )

        # プロンプトに日本人指定を追加
        full_prompt = prompt
        if "Japanese" not in prompt:
            full_prompt = "All people in this image must be Japanese. " + prompt

        # 画像指示を追加
        if image_instructions:
            full_prompt = "\n\n".join(image_instructions) + "\n\n" + full_prompt

        # アスペクト比と解像度の指示を追加
        full_prompt += f"\n\nIMPORTANT: Generate a high-resolution, 4K quality image with {aspect_ratio} aspect ratio. The image should be crisp, detailed, and suitable for professional marketing use."

        # テキストプロンプトを追加
        contents.append(full_prompt)

        # 参照画像を追加（トレーナーを先に、背景を後に）
        # APIの制限を考慮してトレーナー画像は最大3枚に制限
        limited_trainer_images = trainer_images[:3] if len(trainer_images) > 3 else trainer_images
        if len(trainer_images) > 3:
            print(f"   ⚠️ トレーナー画像を{len(trainer_images)}枚から3枚に制限しました")

        for img_info in limited_trainer_images + bg_images:
            image_path = img_info["path"]
            if isinstance(image_path, str):
                image_path = Path(image_path)

            if image_path.exists():
                with open(image_path, "rb") as f:
                    image_bytes = f.read()

                suffix = image_path.suffix.lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.webp': 'image/webp',
                    '.gif': 'image/gif'
                }
                mime_type = mime_types.get(suffix, 'image/jpeg')

                contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
                print(f"   📎 参照画像追加: {img_info['type']} - {image_path.name}")

        print(f"📤 Gemini にリクエスト送信中...")
        print(f"   アスペクト比: {aspect_ratio}")
        print(f"   参照画像数: {len(limited_trainer_images + bg_images)} (トレーナー: {len(limited_trainer_images)}, 背景: {len(bg_images)})")

        # Nano Banana Pro で画像生成
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            )
        )

        print(f"📥 レスポンス受信")

        # レスポンス処理
        text_response = ""
        image_saved = False
        image_path = None

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                text_response += part.text
                print(f"📝 テキスト応答: {part.text[:100]}..." if len(part.text) > 100 else f"📝 テキスト応答: {part.text}")
            elif part.inline_data is not None:
                # 画像データを保存
                image_data = part.inline_data.data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_path = output_dir / f"firefitness_{timestamp}.png"

                # バイトデータとして保存
                with open(image_path, "wb") as f:
                    f.write(image_data)

                image_saved = True
                print(f"💾 画像保存: {image_path}")

        if image_saved:
            return {
                "success": True,
                "image_path": str(image_path),
                "text_response": text_response
            }
        else:
            return {
                "success": False,
                "error": "画像が生成されませんでした",
                "text_response": text_response
            }

    except Exception as e:
        print(f"❌ エラー発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


def generate_image_simple(
    prompt: str,
    aspect_ratio: str = "1:1",
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    参照画像なしでシンプルに画像生成（テスト用）
    """
    return generate_image_with_gemini(
        prompt=prompt,
        reference_images=[],
        aspect_ratio=aspect_ratio,
        output_dir=output_dir
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # テスト
    test_prompt = """
    A professional photograph of a modern personal training studio in Japan.
    A calm consultation scene: a professional Japanese trainer in their 30s is explaining
    something to a Japanese female client in her 30s. Natural light comes through large windows.
    The atmosphere is warm, professional, and inviting. Clean minimal interior design.
    Soft natural lighting, high quality photography.
    """

    print("Testing Gemini 2.0 Flash image generation...")
    result = generate_image_simple(test_prompt, aspect_ratio="16:9")

    if result["success"]:
        print(f"✅ Image saved to: {result['image_path']}")
    else:
        print(f"❌ Error: {result.get('error')}")
