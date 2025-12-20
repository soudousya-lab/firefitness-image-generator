"""
Claude APIを使用したプロンプト変換モジュール
日本語入力 → 最適化された英語プロンプト
FIREFITNESSのブランドガイドラインを反映
"""

import os
import anthropic
from typing import Dict, Any

# FIREFITNESSブランドガイドライン
BRAND_GUIDELINES = """
## FIREFITNESS ブランドガイドライン

### コンセプト
「なぜ変わらないのか」を3軸診断（姿勢×食事×継続）で特定するパーソナルジム。
煽らない、押し付けない、気づきを与える。

### ターゲット
30-50代。派手な筋肉アピールには引く層。落ち着いた、信頼できる雰囲気を好む。

### ブランドカラー
- メイン：#0d2b45（ダークネイビー）
- アクセント：#ff6b35（オレンジ）
- 背景：#f5f5f5（ライトグレー）/ #ffffff（白）

### 写真トーン
明るすぎず暗すぎず、自然光ベース、彩度控えめ、コントラスト控えめ、落ち着いた印象

### 絶対にNGなビジュアル
- ムキムキの筋肉アップ
- 汗だくで叫んでいるトレーニング風景
- 過度なビフォーアフター（半裸の体型比較）
- ギラギラした色使い（金・赤・黒の組み合わせ）
- 「限界突破」「本気」「覚悟」系の煽り文字
- ストックフォト感のある作り笑顔
- HDR風のギラギラした加工
- ネオンカラー

### 目指すべきビジュアル
- 落ち着いた空間で会話しているシーン
- 姿勢をチェックしている専門的な場面
- 自然光、清潔感のある内装
- 「考えている」「説明を聞いている」表情
- 手元や足元のクローズアップ
- 図解・インフォグラフィック

### プロンプトで使うべきキーワード
calm, professional, clean, natural light, consultation, thoughtful, minimal, warm,
soft lighting, genuine smile, attentive, engaged, modern interior, spacious

### プロンプトで避けるべきキーワード
muscular, intense, extreme, sweat, screaming, bodybuilder, six-pack, 
dramatic lighting, HDR, neon, aggressive, pumped, ripped, shredded
"""

SITUATION_PROMPTS = {
    "カウンセリング・相談": {
        "scene": "professional consultation session in a modern personal training studio",
        "action": "having a calm, thoughtful conversation, trainer explaining with gestures, client listening attentively",
        "mood": "professional yet warm, trustworthy atmosphere"
    },
    "姿勢チェック・診断": {
        "scene": "posture assessment area with clean white walls",
        "action": "trainer carefully analyzing client's posture from the side, pointing out alignment",
        "mood": "clinical precision with caring approach"
    },
    "セッション風景（落ち着いた雰囲気）": {
        "scene": "well-lit training area with minimal equipment",
        "action": "gentle guided exercise, trainer providing supportive instruction, controlled movements",
        "mood": "calm, focused, encouraging atmosphere"
    },
    "食事相談・説明": {
        "scene": "consultation area in a modern personal training studio, no food visible",
        "action": "trainer and client having a calm discussion about nutrition, trainer explaining with tablet or paper, gesturing while talking",
        "mood": "educational, supportive, counseling atmosphere similar to general consultation"
    },
    "施設内観（人物なし）": {
        "scene": "clean, modern gym interior with natural light streaming through windows",
        "action": "empty space showcasing equipment arrangement and cleanliness",
        "mood": "inviting, spacious, professional"
    },
    "図解・インフォグラフィック": {
        "scene": "clean background suitable for informational graphics",
        "action": "visual diagram or infographic layout",
        "mood": "clear, educational, professional"
    },
    "目標達成で喜ぶ風景": {
        "scene": "bright training studio with celebratory atmosphere",
        "action": "client showing genuine happiness, trainer congratulating with warm smile, natural celebration",
        "mood": "joyful but not over-the-top, authentic happiness, proud achievement"
    }
}

CLIENT_DESCRIPTIONS = {
    "30代女性": "a Japanese woman in her 30s, professional appearance, wearing comfortable athletic wear",
    "30代男性": "a Japanese man in his 30s, office worker type, wearing casual training clothes",
    "40代女性": "a Japanese woman in her 40s, elegant and health-conscious appearance",
    "40代男性ビジネスマン": "a Japanese businessman in his 40s, slightly tired but motivated expression",
    "50代女性": "a Japanese woman in her 50s, mature and dignified appearance",
    "50代男性": "a Japanese man in his 50s, experienced professional look",
    "シニア女性（60代以上）": "a Japanese senior woman in her 60s, active and healthy appearance",
    "シニア男性（60代以上）": "a Japanese senior man in his 60s, distinguished and active",
    "主婦層": "a Japanese homemaker, warm and approachable appearance, health-conscious"
}

MOOD_MODIFIERS = {
    "落ち着いた": "very calm and serene atmosphere, muted colors, soft diffused lighting",
    "やや落ち着いた": "calm professional atmosphere, natural soft lighting, subtle warmth",
    "ニュートラル": "balanced neutral atmosphere, even lighting",
    "やや活気ある": "gently energetic atmosphere, brighter natural light, subtle dynamism",
    "活気ある": "positive energetic atmosphere, bright natural light, sense of movement"
}


def convert_prompt_with_claude(generation_input: Dict[str, Any]) -> str:
    """
    Claude APIを使用して、入力情報を最適化された画像生成プロンプトに変換
    
    Args:
        generation_input: 画像生成の入力情報
            - location: 店舗名
            - situation: シチュエーション
            - trainer: トレーナー名（オプション）
            - client: クライアントタイプ（オプション）
            - aspect_ratio: アスペクト比
            - resolution: 解像度
            - additional_prompt: 追加指示
            - image_text: 画像内テキスト（オプション）
            - mood: 雰囲気
    
    Returns:
        最適化された英語プロンプト
    """
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # 入力情報を整理
    situation = generation_input.get("situation", "カウンセリング・相談")
    situation_info = SITUATION_PROMPTS.get(situation, SITUATION_PROMPTS["カウンセリング・相談"])
    
    trainer_name = generation_input.get("trainer")
    client_type = generation_input.get("client")
    client_desc = CLIENT_DESCRIPTIONS.get(client_type, "") if client_type else ""
    
    mood = generation_input.get("mood", "やや落ち着いた")
    mood_desc = MOOD_MODIFIERS.get(mood, MOOD_MODIFIERS["やや落ち着いた"])
    
    additional = generation_input.get("additional_prompt", "")
    image_text = generation_input.get("image_text")
    location = generation_input.get("location", "島田本町")
    
    # Claude への指示
    system_prompt = f"""あなたは画像生成AI（Gemini）用のプロンプトを作成する専門家です。
FIREFITNESSというパーソナルトレーニングジムのマーケティング画像を生成するためのプロンプトを作成します。

{BRAND_GUIDELINES}

## あなたのタスク
1. 入力された日本語の指示を理解する
2. ブランドガイドラインに完全に沿った英語プロンプトを生成する
3. NGワードは絶対に使わない
4. 推奨キーワードを積極的に使用する
5. 具体的で視覚的な描写を含める
6. 【重要】登場人物は全員日本人（Japanese）であることを明記する。プロンプトの冒頭に "All people in this image must be Japanese." を必ず含める

## 出力形式
英語のプロンプトのみを出力してください。説明や注釈は不要です。
プロンプトは1つの段落で、以下の要素を含めてください：
- シーン設定（場所、環境）
- 人物描写（いる場合）
- アクション/ポーズ
- 光と雰囲気
- カメラアングル/構図
- スタイル指定（写真風、イラスト等）
"""

    # ユーザーメッセージを構築
    user_message = f"""以下の条件で画像生成プロンプトを作成してください：

【店舗】{location}店（背景画像を参照して使用）
【シチュエーション】{situation}
- シーン: {situation_info['scene']}
- アクション: {situation_info['action']}
- 基本ムード: {situation_info['mood']}

【登場人物】
"""
    
    if trainer_name:
        user_message += f"- トレーナー: {trainer_name}（参照画像のトレーナーを登場させる。特徴を維持すること）\n"
    
    if client_desc:
        user_message += f"- クライアント: {client_desc}\n"
    
    if not trainer_name and not client_desc:
        user_message += "- 人物なし（施設のみ）\n"
    
    user_message += f"""
【雰囲気】{mood}
- {mood_desc}

【追加指示】
{additional if additional else "特になし"}
"""
    
    if image_text:
        user_message += f"""
【画像内テキスト】
"{image_text}" というテキストを画像内に含める
"""
    
    user_message += """
【重要な注意事項】
1. 参照画像（背景・トレーナー）がある場合、それらを活かしたプロンプトにする
2. 「この背景を使用」「このトレーナーの外見を維持」という指示を含める
3. 日本のパーソナルジムらしい雰囲気を出す
4. 自然光、清潔感を強調
5. 絶対にNGワード（muscular, intense, extreme, sweat, screaming等）を使わない
"""

    # Claude API 呼び出し
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": user_message}
        ],
        system=system_prompt
    )
    
    return message.content[0].text


def build_simple_prompt(generation_input: Dict[str, Any]) -> str:
    """
    Claude APIを使わずにシンプルなプロンプトを構築（フォールバック用）
    """
    situation = generation_input.get("situation", "カウンセリング・相談")
    situation_info = SITUATION_PROMPTS.get(situation, SITUATION_PROMPTS["カウンセリング・相談"])
    
    trainer_name = generation_input.get("trainer")
    client_type = generation_input.get("client")
    client_desc = CLIENT_DESCRIPTIONS.get(client_type, "") if client_type else ""
    
    mood = generation_input.get("mood", "やや落ち着いた")
    mood_desc = MOOD_MODIFIERS.get(mood, MOOD_MODIFIERS["やや落ち着いた"])
    
    parts = []
    
    # シーン
    parts.append(f"A professional photograph of {situation_info['scene']}.")
    
    # 人物
    if trainer_name:
        parts.append(f"The trainer from the reference image is present, maintaining their exact appearance.")
    
    if client_desc:
        parts.append(f"A client: {client_desc}.")
    
    # アクション
    parts.append(f"Scene: {situation_info['action']}.")
    
    # 雰囲気
    parts.append(f"Atmosphere: {mood_desc}.")
    parts.append(situation_info['mood'])
    
    # スタイル
    parts.append("Style: natural lighting, clean modern interior, soft colors, professional photography, "
                "warm and inviting atmosphere, high quality, detailed, realistic.")
    
    # 参照画像の指示
    parts.append("Use the provided background image as the setting. "
                "If trainer reference images are provided, maintain their exact facial features and appearance.")
    
    return " ".join(parts)


if __name__ == "__main__":
    # テスト
    test_input = {
        "location": "島田本町",
        "situation": "カウンセリング・相談",
        "trainer": "岡田",
        "client": "30代女性",
        "mood": "やや落ち着いた",
        "additional_prompt": "窓から自然光が入っている、和やかな雰囲気"
    }
    
    print("=== シンプルプロンプト（フォールバック）===")
    print(build_simple_prompt(test_input))
    print()
    
    # Claude API テスト（APIキーが設定されている場合）
    if os.getenv("ANTHROPIC_API_KEY"):
        print("=== Claude API 最適化プロンプト ===")
        print(convert_prompt_with_claude(test_input))
