"""
Claude APIを使用したプロンプト変換モジュール
日本語入力 → 最適化された英語プロンプト
FIREFITNESSのブランドガイドラインを反映
宣材写真 + SNS投稿画像 両対応
AIによるコンテンツ自動生成機能
"""

import os
import anthropic
from typing import Dict, Any, List
import json

# =====================================
# FIREFITNESSコアバリュー（価値基準）
# =====================================

FIREFITNESS_CORE_VALUES = """
## FIREFITNESSが提供する価値

### 独自の強み：3軸診断
「なぜ変わらないのか」を3つの軸で特定し、根本からアプローチ

1. **姿勢軸** - 体の土台を整える
   - 姿勢の歪みが運動効率を下げる
   - 正しいフォームで怪我を防ぐ
   - 見た目の印象も変わる

2. **食事軸** - 無理なく続ける食習慣
   - 極端な制限はしない
   - 生活に合わせた現実的な提案
   - 知識を身につけて自分でできるように

3. **継続軸** - 習慣化のメカニズム
   - 意志の力に頼らない仕組み
   - 心理学に基づいたアプローチ
   - 小さな成功体験を積み重ねる

### FIREFITNESSの特徴
- 完全個室・マンツーマン
- 煽らない、押し付けない
- 気づきを与える指導スタイル
- 根本原因から解決する
- 一人ひとりに合わせたオーダーメイド

### ターゲット層の悩み（共感ポイント）
- ジムに通っても続かなかった
- 食事制限してもリバウンドした
- 何から始めればいいかわからない
- 自己流では効果が出ない
- 忙しくて時間が取れない
- 年齢とともに痩せにくくなった
- 姿勢が悪くて肩こり・腰痛がある

### 提供できる結果
- 体重・体型の変化
- 姿勢改善による見た目の変化
- 肩こり・腰痛の改善
- 運動習慣の定着
- 食事の知識と自己管理能力
- 自信の向上
- 健康診断の数値改善

### 伝えるべきメッセージのトーン
- 共感から入る（あなたのせいじゃない）
- 原因を明確にする（だから続かなかった）
- 解決策を示す（FIREFITNESSなら）
- 行動を促す（まずは無料カウンセリングへ）
"""

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

# =====================================
# SNS投稿用の設定
# =====================================

SNS_LAYOUT_PROMPTS = {
    "text_centered": {
        "description": "text-focused graphic design with centered typography",
        "elements": "clean white or light background, prominent centered text, minimal design elements",
        "style": "modern Japanese typography, clean sans-serif font, elegant spacing"
    },
    "infographic": {
        "description": "informational graphic with icons and structured layout",
        "elements": "icon-based design, visual hierarchy, organized sections, educational layout",
        "style": "flat design icons, clean lines, navy blue and orange color scheme"
    },
    "photo_with_text": {
        "description": "photograph as main element with text overlay",
        "elements": "photo background with semi-transparent overlay, text positioned for readability",
        "style": "professional photo with subtle text integration"
    },
    "card_layout": {
        "description": "card-based design with organized information blocks",
        "elements": "multiple card sections, clean borders, structured data presentation",
        "style": "modern dashboard-like layout, clean separations"
    },
    "testimonial": {
        "description": "customer quote or testimonial design",
        "elements": "large quotation marks, quote text prominently displayed, attribution at bottom",
        "style": "elegant quote design, warm and trustworthy feeling"
    },
    "step_by_step": {
        "description": "numbered steps or process flow design",
        "elements": "numbered circles, sequential layout, clear progression",
        "style": "educational how-to format, easy to follow"
    },
    "before_after_numbers": {
        "description": "numerical comparison or achievement display",
        "elements": "large numbers prominently displayed, comparison indicators",
        "style": "impactful number presentation without body photos"
    },
    "qa_format": {
        "description": "question and answer format design",
        "elements": "large Q letter in accent color, question text, answer section",
        "style": "FAQ style, clear question-answer separation"
    }
}

SNS_POST_TYPE_PROMPTS = {
    # Google Map用
    "3axis_intro": {
        "theme": "3-axis diagnosis introduction (posture, nutrition, continuity)",
        "visual": "three icons in a row representing posture (standing figure), nutrition (fork and knife), continuity (brain)",
        "text_hint": "姿勢軸、食事軸、継続軸"
    },
    "customer_success": {
        "theme": "customer success story and achievement",
        "visual": "achievement numbers like '-5kg / 3ヶ月', success metrics",
        "text_hint": "お客様の成果、達成した数値"
    },
    "facility_intro": {
        "theme": "facility and equipment introduction",
        "visual": "clean gym interior, private training space, natural light",
        "text_hint": "完全個室、プライベート空間"
    },
    "trainer_intro": {
        "theme": "trainer introduction and expertise",
        "visual": "professional trainer silhouette or consultation scene",
        "text_hint": "トレーナー紹介、専門分野"
    },
    "faq": {
        "theme": "frequently asked questions",
        "visual": "large Q letter, question text, professional answer design",
        "text_hint": "よくある質問、Q&A"
    },
    "health_tips": {
        "theme": "health and fitness knowledge tips",
        "visual": "educational infographic, simple illustration of health topic",
        "text_hint": "健康豆知識、💡知ってましたか？"
    },
    "availability": {
        "theme": "schedule and campaign information",
        "visual": "calendar or schedule graphic, availability indicators",
        "text_hint": "空き状況、予約受付中"
    },
    # Instagram用
    "education": {
        "theme": "educational content, self-check, knowledge sharing",
        "visual": "step-by-step instruction, numbered list, educational illustration",
        "text_hint": "セルフチェック、〜の方法"
    },
    "empathy": {
        "theme": "empathy and problem-solution content",
        "visual": "relatable text-based design, problem statement followed by solution hint",
        "text_hint": "「〜が続かない」本当の理由、悩み→解決"
    },
    "trust": {
        "theme": "trust-building, customer testimonials, results",
        "visual": "quote design, testimonial format, trust indicators",
        "text_hint": "お客様の声、実績紹介"
    }
}

BACKGROUND_STYLE_PROMPTS = {
    "solid": "solid color background",
    "gradient": "smooth gradient background",
    "photo": "photographic background with overlay"
}

TEXT_SIZE_PROMPTS = {
    "xs": "very small, subtle text",
    "small": "small, secondary text",
    "medium": "medium-sized, readable text",
    "large": "large, prominent text",
    "xl": "very large, headline text",
    "xxl": "extra large, dominant text"
}

POSITION_PROMPTS = {
    "top": "positioned at the top of the image",
    "center": "centered in the image",
    "bottom": "positioned at the bottom of the image",
    "top_left": "positioned in the top-left corner",
    "top_right": "positioned in the top-right corner",
    "bottom_left": "positioned in the bottom-left corner",
    "bottom_right": "positioned in the bottom-right corner"
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


def convert_sns_prompt_with_claude(sns_params: Dict[str, Any]) -> str:
    """
    SNS投稿用の画像生成プロンプトを作成

    Args:
        sns_params: SNS投稿の詳細設定
            - platform: Google Map / Instagram
            - post_type: 投稿タイプ
            - layout_style: レイアウトスタイル
            - background_style: 背景スタイル
            - custom_opacity: 透明度
            - main_headline: 見出し
            - headline_color: 見出し色
            - headline_size: 見出しサイズ
            - headline_position: 見出し位置
            - sub_text: サブテキスト
            - accent_text: アクセントテキスト
            - include_logo: ロゴ含むか
            - logo_position: ロゴ位置
            - include_trainer_photo: トレーナー写真含むか
            - trainer_photo_style: トレーナー写真スタイル
            - include_icons: アイコン含むか
            - icon_type: アイコンタイプ
            - font_style: フォントスタイル
            - border_style: 枠線スタイル
            - decoration: 装飾要素
            - overall_mood: 全体雰囲気
            - color_intensity: 色の強さ

    Returns:
        最適化された英語プロンプト
    """

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # パラメータを取得
    platform = sns_params.get("platform", "Instagram")
    post_type = sns_params.get("post_type", "")
    layout_style = sns_params.get("layout_style", "テキスト中心（シンプル）")
    background_style = sns_params.get("background_style", "単色（白）")
    custom_opacity = sns_params.get("custom_opacity", 100)

    main_headline = sns_params.get("main_headline", "")
    headline_color = sns_params.get("headline_color", "#0d2b45")
    headline_size = sns_params.get("headline_size", "large")
    headline_position = sns_params.get("headline_position", "center")

    sub_text = sns_params.get("sub_text", "")
    sub_text_color = sns_params.get("sub_text_color", "#0d2b45")

    accent_text = sns_params.get("accent_text", "")
    accent_style = sns_params.get("accent_style", "")

    include_logo = sns_params.get("include_logo", True)
    logo_position = sns_params.get("logo_position", "bottom_right")
    logo_size = sns_params.get("logo_size", "medium")

    include_trainer_photo = sns_params.get("include_trainer_photo", False)
    trainer_photo_style = sns_params.get("trainer_photo_style", "")

    include_icons = sns_params.get("include_icons", False)
    icon_type = sns_params.get("icon_type", "")
    custom_icons = sns_params.get("custom_icons", "")

    font_style = sns_params.get("font_style", "ゴシック体（モダン）")
    border_style = sns_params.get("border_style", "なし")
    decoration = sns_params.get("decoration", [])
    overall_mood = sns_params.get("overall_mood", "やや落ち着いた")
    color_intensity = sns_params.get("color_intensity", "標準")

    # レイアウト情報を取得
    layout_key = {
        "テキスト中心（シンプル）": "text_centered",
        "図解・インフォグラフィック": "infographic",
        "写真メイン＋テキスト": "photo_with_text",
        "カード型（情報整理）": "card_layout",
        "引用・お客様の声": "testimonial",
        "ステップ・手順説明": "step_by_step",
        "ビフォーアフター風（数値）": "before_after_numbers",
        "Q&A形式": "qa_format"
    }.get(layout_style, "text_centered")

    layout_info = SNS_LAYOUT_PROMPTS.get(layout_key, SNS_LAYOUT_PROMPTS["text_centered"])

    # 投稿タイプ情報を取得
    post_type_key = ""
    for pt_name, pt_key in [
        ("月曜：3軸診断の紹介", "3axis_intro"),
        ("火曜：お客様の成果報告", "customer_success"),
        ("水曜：施設・設備の紹介", "facility_intro"),
        ("木曜：トレーナー紹介", "trainer_intro"),
        ("金曜：よくある質問", "faq"),
        ("土曜：健康・運動の豆知識", "health_tips"),
        ("日曜：空き状況・キャンペーン", "availability"),
        ("教育系：セルフチェック・知識", "education"),
        ("共感系：悩み→解決", "empathy"),
        ("信頼系：お客様の声・実績", "trust")
    ]:
        if pt_name in post_type:
            post_type_key = pt_key
            break

    post_type_info = SNS_POST_TYPE_PROMPTS.get(post_type_key, {})

    # システムプロンプト
    system_prompt = f"""あなたはSNS投稿用の画像生成プロンプトを作成する専門家です。
FIREFITNESSというパーソナルトレーニングジムのSNS投稿画像を生成するためのプロンプトを作成します。

{BRAND_GUIDELINES}

## SNS投稿画像の特徴
- 情報発信系の画像（テキスト+デザイン要素）
- 文字が読みやすく、メッセージが明確
- プロフェッショナルなグラフィックデザイン
- 日本語テキストを含む画像
- FIREFITNESSのブランドカラー（ネイビー#0d2b45、オレンジ#ff6b35）を活用

## 重要な制約
1. 日本語テキストを画像内に正確に配置する指示を含める
2. ブランドカラーを正しく使用する
3. 読みやすさと視覚的インパクトのバランスを取る
4. NGビジュアル（ギラギラ、筋肉アップ等）は絶対に避ける
5. ロゴ「FIREFITNESS」を指定位置に含める指示（必要な場合）

## 出力形式
英語のプロンプトのみを出力してください。
プロンプトは1つの段落で、以下の要素を詳細に含めてください：
- 全体のレイアウト構造
- 背景スタイル（色、グラデーション、透明度）
- テキスト要素（内容、位置、サイズ、色、フォントスタイル）
- アイコン・図解要素（ある場合）
- ロゴ配置（ある場合）
- 装飾要素（枠線、影など）
- 全体の雰囲気とスタイル
"""

    # ユーザーメッセージを構築
    user_message = f"""以下の条件でSNS投稿用画像の生成プロンプトを作成してください：

【プラットフォーム】{platform}
【投稿タイプ】{post_type}
"""

    if post_type_info:
        user_message += f"""- テーマ: {post_type_info.get('theme', '')}
- 視覚的要素: {post_type_info.get('visual', '')}
"""

    user_message += f"""
【レイアウト】{layout_style}
- 説明: {layout_info['description']}
- 要素: {layout_info['elements']}
- スタイル: {layout_info['style']}

【背景設定】
- スタイル: {background_style}
"""

    if "写真背景" in background_style:
        user_message += f"- オーバーレイ透明度: {custom_opacity}%（背景を{100-custom_opacity}%暗くまたは明るく）\n"

    user_message += f"""
【テキスト設定】
"""

    if main_headline:
        size_desc = TEXT_SIZE_PROMPTS.get(headline_size, "large text")
        pos_desc = POSITION_PROMPTS.get(headline_position, "centered")
        user_message += f"""- 見出し: "{main_headline}"
  - 色: {headline_color}
  - サイズ: {size_desc}
  - 位置: {pos_desc}
"""

    if sub_text:
        user_message += f"""- サブテキスト: "{sub_text}"
  - 色: {sub_text_color}
"""

    if accent_text:
        user_message += f"""- アクセントテキスト: "{accent_text}"
  - スタイル: {accent_style}
"""

    user_message += f"""
【ロゴ設定】
"""
    if include_logo:
        pos_desc = POSITION_PROMPTS.get(logo_position, "bottom-right corner")
        size_desc = TEXT_SIZE_PROMPTS.get(logo_size, "medium")
        user_message += f"""- FIREFITNESSロゴを含める
  - 位置: {pos_desc}
  - サイズ: {size_desc}
"""
    else:
        user_message += "- ロゴなし\n"

    if include_trainer_photo:
        user_message += f"""
【トレーナー写真】
- スタイル: {trainer_photo_style}
- 参照画像のトレーナーの外見を維持
"""

    if include_icons:
        user_message += f"""
【アイコン・図解】
- タイプ: {icon_type}
"""
        if custom_icons:
            user_message += f"- カスタム説明: {custom_icons}\n"

    user_message += f"""
【デザイン詳細】
- フォントスタイル: {font_style}
- 枠線: {border_style}
- 装飾要素: {', '.join(decoration) if decoration else 'なし'}
- 全体の雰囲気: {overall_mood}
- 色の強さ: {color_intensity}

【重要な注意事項】
1. 日本語テキストを正確に配置する指示を含める
2. テキストが読みやすいよう、背景とのコントラストを確保
3. FIREFITNESSのブランドカラー（ネイビー#0d2b45、オレンジ#ff6b35）を効果的に使用
4. プロフェッショナルで落ち着いたデザインを心がける
5. SNSで目を引きつつも、派手すぎないバランス
6. 日本のパーソナルジムのSNS投稿らしい雰囲気
"""

    # Claude API 呼び出し
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[
            {"role": "user", "content": user_message}
        ],
        system=system_prompt
    )

    return message.content[0].text


def generate_sns_content_with_claude(
    theme: str,
    page_type: str,
    page_number: int = 1,
    total_pages: int = 1,
    previous_content: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Claude APIを使用して、FIREFITNESSの価値基準に基づいた
    SNS投稿コンテンツを自動生成

    Args:
        theme: 投稿テーマ（例：「ダイエットが続かない理由」）
        page_type: ページタイプ（title, problem, cause, solution等）
        page_number: 現在のページ番号
        total_pages: 総ページ数
        previous_content: 前のページで生成されたコンテンツ（一貫性のため）

    Returns:
        Dict: {
            "headline": str,  # メイン見出し
            "sub_text": str,  # サブテキスト
            "accent_text": str,  # アクセントテキスト
            "body_points": List[str],  # 本文ポイント（箇条書き用）
            "cta_text": str,  # コールトゥアクション
            "icon_suggestion": str,  # 推奨アイコン
            "layout_suggestion": str,  # 推奨レイアウト
        }
    """

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        # フォールバック：デフォルトコンテンツを返す
        return _get_fallback_content(theme, page_type)

    client = anthropic.Anthropic(api_key=api_key)

    # ページタイプごとの役割
    page_type_roles = {
        "title": "タイトルページ - 読者の興味を引く、インパクトのある見出し",
        "problem": "問題提起 - 読者が共感できる悩みを提示",
        "cause": "原因説明 - なぜその問題が起きるのか、本当の理由",
        "solution": "解決策提示 - FIREFITNESSならではの解決アプローチ",
        "detail": "詳細説明 - 具体的な方法やポイントを説明",
        "evidence": "根拠・実績 - 信頼性を高めるエビデンス",
        "summary": "まとめ - 要点の整理と振り返り",
        "cta": "行動喚起 - 無料カウンセリングへの誘導"
    }

    page_role = page_type_roles.get(page_type, "一般的な情報提供")

    # システムプロンプト
    system_prompt = f"""あなたはFIREFITNESSのSNS投稿コンテンツを作成する専門家です。

{FIREFITNESS_CORE_VALUES}

## あなたの役割
FIREFITNESSの価値観（3軸診断：姿勢・食事・継続）を崩さず、
毎回新鮮で価値のあるコンテンツを生成してください。

## 重要なルール
1. FIREFITNESSの独自性（3軸診断）を必ず反映
2. 煽らない、押し付けない、寄り添うトーン
3. 共感から入り、原因を説明し、解決策を示す流れ
4. 専門的すぎず、一般の人にわかりやすい言葉
5. 短く、SNSで読みやすい文量
6. ターゲット層（30-50代、派手さを嫌う層）に響く表現

## 出力形式
必ず以下のJSON形式で出力してください（他のテキストは不要）:
{{
    "headline": "メイン見出し（15文字以内推奨）",
    "sub_text": "サブテキスト（30文字以内推奨）",
    "accent_text": "強調したいキーワード（5文字以内）",
    "body_points": ["ポイント1", "ポイント2", "ポイント3"],
    "cta_text": "行動喚起テキスト（CTAページ用）",
    "icon_suggestion": "推奨アイコン種類",
    "layout_suggestion": "推奨レイアウト"
}}
"""

    # 前のコンテンツを考慮
    previous_context = ""
    if previous_content:
        previous_context = "\n【前のページの内容（一貫性を保つこと）】\n"
        for prev in previous_content:
            previous_context += f"- {prev.get('page_type', '')}: {prev.get('headline', '')}\n"

    # ユーザーメッセージ
    user_message = f"""以下の条件でSNS投稿コンテンツを生成してください：

【テーマ】{theme}
【ページタイプ】{page_type}（{page_role}）
【ページ番号】{page_number} / {total_pages}
{previous_context}

このページでは「{page_role}」を担当します。
テーマ「{theme}」に沿って、FIREFITNESSの価値観を反映したコンテンツを生成してください。

重要：
- headline, sub_text, accent_text は必ず日本語で
- SNSで目を引く、でも煽りすぎないバランス
- FIREFITNESSらしい「寄り添い」のトーン
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": user_message}
            ],
            system=system_prompt
        )

        response_text = message.content[0].text

        # JSONを抽出してパース
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            content = json.loads(json_match.group())
            return content
        else:
            return _get_fallback_content(theme, page_type)

    except Exception as e:
        print(f"AI content generation error: {e}")
        return _get_fallback_content(theme, page_type)


def _get_fallback_content(theme: str, page_type: str) -> Dict[str, Any]:
    """
    API呼び出し失敗時のフォールバックコンテンツ
    """
    fallback_contents = {
        "title": {
            "headline": theme if theme else "カラダが変わる理由",
            "sub_text": "FIREFITNESSの3軸診断",
            "accent_text": "3軸",
            "body_points": [],
            "cta_text": "",
            "icon_suggestion": "diagnostic",
            "layout_suggestion": "text_centered"
        },
        "problem": {
            "headline": "こんなお悩みありませんか？",
            "sub_text": "多くの方が同じ壁にぶつかっています",
            "accent_text": "悩み",
            "body_points": ["ジムに通っても続かない", "食事制限してもリバウンド", "何から始めればいいかわからない"],
            "cta_text": "",
            "icon_suggestion": "question",
            "layout_suggestion": "card_layout"
        },
        "cause": {
            "headline": "それ、あなたのせいじゃありません",
            "sub_text": "続かない本当の理由",
            "accent_text": "原因",
            "body_points": ["意志の弱さではない", "方法が合っていなかった", "根本原因を見逃していた"],
            "cta_text": "",
            "icon_suggestion": "lightbulb",
            "layout_suggestion": "step_by_step"
        },
        "solution": {
            "headline": "3軸診断で根本から変える",
            "sub_text": "姿勢 × 食事 × 継続",
            "accent_text": "解決",
            "body_points": ["姿勢軸：体の土台を整える", "食事軸：無理なく続く習慣", "継続軸：仕組み化で習慣に"],
            "cta_text": "",
            "icon_suggestion": "three_axis",
            "layout_suggestion": "infographic"
        },
        "detail": {
            "headline": "具体的なアプローチ",
            "sub_text": "あなたに合わせたオーダーメイド",
            "accent_text": "方法",
            "body_points": ["一人ひとりの原因を特定", "生活に合わせた現実的な提案", "小さな成功体験を積み重ねる"],
            "cta_text": "",
            "icon_suggestion": "checklist",
            "layout_suggestion": "card_layout"
        },
        "evidence": {
            "headline": "お客様の声",
            "sub_text": "実際に変化を感じた方々",
            "accent_text": "実績",
            "body_points": ["3ヶ月で姿勢が改善", "無理なく5kg減量", "運動が習慣になった"],
            "cta_text": "",
            "icon_suggestion": "testimonial",
            "layout_suggestion": "testimonial"
        },
        "summary": {
            "headline": "まとめ",
            "sub_text": "大切なポイント",
            "accent_text": "要点",
            "body_points": ["原因を特定することが大切", "3つの軸でアプローチ", "無理なく続けられる"],
            "cta_text": "",
            "icon_suggestion": "summary",
            "layout_suggestion": "card_layout"
        },
        "cta": {
            "headline": "まずは無料カウンセリングへ",
            "sub_text": "あなたの「変わらない理由」を見つけます",
            "accent_text": "無料",
            "body_points": [],
            "cta_text": "プロフィールのリンクから予約",
            "icon_suggestion": "arrow",
            "layout_suggestion": "text_centered"
        }
    }

    return fallback_contents.get(page_type, fallback_contents["title"])


def generate_theme_variations(base_theme: str, count: int = 5) -> List[str]:
    """
    ベーステーマから複数のバリエーションを生成

    Args:
        base_theme: 基本テーマ（例：「ダイエット」）
        count: 生成するバリエーション数

    Returns:
        テーマバリエーションのリスト
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return [base_theme] * count

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = f"""あなたはFIREFITNESSのSNSコンテンツ企画者です。

{FIREFITNESS_CORE_VALUES}

ベーステーマから、FIREFITNESSの価値観に合った投稿テーマのバリエーションを生成してください。
煽らない、寄り添う、共感を得るトーンで。

出力形式：JSON配列のみ（説明不要）
["テーマ1", "テーマ2", ...]
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {"role": "user", "content": f"ベーステーマ「{base_theme}」から{count}個のバリエーションを生成してください。"}
            ],
            system=system_prompt
        )

        response_text = message.content[0].text
        import re
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            return json.loads(json_match.group())
        return [base_theme] * count

    except Exception as e:
        print(f"Theme variation generation error: {e}")
        return [base_theme] * count


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


def build_simple_sns_prompt(sns_params: Dict[str, Any]) -> str:
    """
    Claude APIを使わずにシンプルなSNSプロンプトを構築（フォールバック用）
    """
    parts = []

    # 基本構造
    parts.append("A professional SNS post graphic for a Japanese personal training gym.")

    # レイアウト
    layout = sns_params.get("layout_style", "テキスト中心（シンプル）")
    parts.append(f"Layout style: {layout}.")

    # 背景
    bg = sns_params.get("background_style", "単色（白）")
    if "写真背景" in bg:
        opacity = sns_params.get("custom_opacity", 50)
        parts.append(f"Photo background with {100-opacity}% dark overlay for text readability.")
    else:
        parts.append(f"Background: {bg}.")

    # テキスト
    headline = sns_params.get("main_headline", "")
    if headline:
        parts.append(f'Main headline text: "{headline}" in large, prominent font.')

    sub_text = sns_params.get("sub_text", "")
    if sub_text:
        parts.append(f'Secondary text: "{sub_text}".')

    # ロゴ
    if sns_params.get("include_logo", True):
        pos = sns_params.get("logo_position", "bottom_right")
        parts.append(f"FIREFITNESS logo placed at {pos}.")

    # カラー
    parts.append("Color scheme: navy blue (#0d2b45) and orange (#ff6b35) accents on white/light background.")

    # スタイル
    parts.append("Clean, professional Japanese design. Modern typography. Calm, trustworthy atmosphere.")

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

    # SNSテスト
    test_sns = {
        "platform": "Instagram",
        "post_type": "共感系：悩み→解決",
        "layout_style": "テキスト中心（シンプル）",
        "background_style": "単色（白）",
        "main_headline": "「ジムが続かない」本当の理由",
        "sub_text": "意志の弱さではありません",
        "include_logo": True,
        "logo_position": "bottom_right"
    }

    print("=== SNSシンプルプロンプト（フォールバック）===")
    print(build_simple_sns_prompt(test_sns))
    print()

    # Claude API テスト（APIキーが設定されている場合）
    if os.getenv("ANTHROPIC_API_KEY"):
        print("=== Claude API 最適化プロンプト ===")
        print(convert_prompt_with_claude(test_input))
        print()
        print("=== Claude API SNSプロンプト ===")
        print(convert_sns_prompt_with_claude(test_sns))
