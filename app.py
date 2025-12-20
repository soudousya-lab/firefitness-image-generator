"""
FIREFITNESS 画像生成アプリ
Streamlit + Claude API + Gemini API
宣材写真 + SNS投稿画像 両対応
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from prompt_converter import convert_prompt_with_claude, convert_sns_prompt_with_claude, generate_sns_content_with_claude
from image_generator import generate_image_with_gemini
import base64
from datetime import datetime

# 環境変数読み込み（ローカル用）
load_dotenv(override=True)

# Streamlit Cloud Secrets対応
# st.secretsがあればos.environに設定（os.getenv()で読めるようにする）
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    pass  # ローカル環境では st.secrets がないのでスキップ

# ページ設定
st.set_page_config(
    page_title="FIREFITNESS 画像生成ツール",
    page_icon="https://fav.farm/%F0%9F%94%A5",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS（テック系企業風・ネイビーベース）
st.markdown("""
<style>
    /* ===== 基本設定 ===== */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #0d2b45 50%, #0f3352 100%);
        font-family: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ===== サイドバー ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d2b45 0%, #081c30 100%);
        border-right: 1px solid rgba(255, 107, 53, 0.2);
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: #e8eef4;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 500;
        letter-spacing: 0.02em;
    }

    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stRadio label {
        color: #b8c9d9 !important;
        font-weight: 400;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 107, 53, 0.3);
    }

    /* ===== メインコンテンツ ===== */
    .main .block-container {
        padding-top: 2rem;
    }

    /* ヘッダー */
    .main-header {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .sub-header {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.95rem;
        font-weight: 300;
        letter-spacing: 0.03em;
        margin-bottom: 2rem;
    }

    /* 見出し */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
        font-weight: 500;
    }

    .stMarkdown p, .stMarkdown li {
        color: #d0dbe6;
    }

    /* ===== タブ ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(13, 43, 69, 0.6);
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 0.5rem 0;
        gap: 4px;
        border-bottom: 2px solid rgba(255, 107, 53, 0.4);
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255, 255, 255, 0.6);
        border: none;
        border-radius: 6px 6px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.02em;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 107, 53, 0.15);
        color: #ffffff;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(255, 107, 53, 0.25) !important;
        color: #ff6b35 !important;
        border-bottom: 2px solid #ff6b35;
    }

    .stTabs [data-baseweb="tab-panel"] {
        background: rgba(8, 28, 48, 0.5);
        border-radius: 0 0 8px 8px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 107, 53, 0.1);
        border-top: none;
    }

    /* ===== フォーム要素 ===== */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(8, 28, 48, 0.8) !important;
        border: 1px solid rgba(255, 107, 53, 0.2) !important;
        border-radius: 6px !important;
        color: #ffffff !important;
        transition: all 0.2s ease;
    }

    .stSelectbox > div > div:hover,
    .stMultiSelect > div > div:hover,
    .stTextInput > div > div > input:hover,
    .stTextArea > div > div > textarea:hover {
        border-color: rgba(255, 107, 53, 0.5) !important;
    }

    .stSelectbox > div > div:focus-within,
    .stMultiSelect > div > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #ff6b35 !important;
        box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.2) !important;
    }

    .stSelectbox label,
    .stMultiSelect label,
    .stTextInput label,
    .stTextArea label,
    .stSlider label,
    .stCheckbox label {
        color: #b8c9d9 !important;
        font-weight: 400;
        font-size: 0.9rem;
    }

    /* プレースホルダー */
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(184, 201, 217, 0.5) !important;
    }

    /* チェックボックス */
    .stCheckbox > label > span {
        color: #d0dbe6 !important;
    }

    /* スライダー */
    .stSlider > div > div > div > div {
        background: #ff6b35 !important;
    }

    /* ===== ボタン ===== */
    .stButton > button {
        background: linear-gradient(135deg, #ff6b35 0%, #e55a2b 100%);
        color: #ffffff;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 2rem;
        font-size: 0.95rem;
        letter-spacing: 0.03em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #ff7a4a 0%, #ff6b35 100%);
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.4);
        transform: translateY(-1px);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* プライマリボタン */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff6b35 0%, #e55a2b 100%);
    }

    /* ===== 情報ボックス ===== */
    .stAlert {
        background: rgba(13, 43, 69, 0.8) !important;
        border: 1px solid rgba(255, 107, 53, 0.3) !important;
        border-radius: 8px !important;
        color: #e8eef4 !important;
    }

    .stAlert > div {
        color: #e8eef4 !important;
    }

    /* 成功メッセージ */
    .stSuccess {
        background: rgba(39, 174, 96, 0.15) !important;
        border: 1px solid rgba(39, 174, 96, 0.4) !important;
    }

    /* エラーメッセージ */
    .stError {
        background: rgba(231, 76, 60, 0.15) !important;
        border: 1px solid rgba(231, 76, 60, 0.4) !important;
    }

    /* 警告メッセージ */
    .stWarning {
        background: rgba(241, 196, 15, 0.15) !important;
        border: 1px solid rgba(241, 196, 15, 0.4) !important;
    }

    /* ===== エキスパンダー ===== */
    .streamlit-expanderHeader {
        background: rgba(13, 43, 69, 0.6) !important;
        border: 1px solid rgba(255, 107, 53, 0.2) !important;
        border-radius: 6px !important;
        color: #ffffff !important;
        font-weight: 500;
    }

    .streamlit-expanderHeader:hover {
        border-color: rgba(255, 107, 53, 0.4) !important;
    }

    .streamlit-expanderContent {
        background: rgba(8, 28, 48, 0.5) !important;
        border: 1px solid rgba(255, 107, 53, 0.1) !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
    }

    /* ===== 区切り線 ===== */
    hr {
        border-color: rgba(255, 107, 53, 0.2) !important;
    }

    /* ===== スピナー ===== */
    .stSpinner > div {
        border-top-color: #ff6b35 !important;
    }

    /* ===== ダウンロードボタン ===== */
    .stDownloadButton > button {
        background: transparent !important;
        border: 2px solid #ff6b35 !important;
        color: #ff6b35 !important;
    }

    .stDownloadButton > button:hover {
        background: rgba(255, 107, 53, 0.1) !important;
    }

    /* ===== コードブロック ===== */
    .stCodeBlock {
        background: rgba(8, 28, 48, 0.9) !important;
        border: 1px solid rgba(255, 107, 53, 0.2) !important;
        border-radius: 6px !important;
    }

    /* ===== 画像 ===== */
    .stImage {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    /* ===== ラジオボタン ===== */
    .stRadio > div {
        background: transparent;
    }

    .stRadio > div > label {
        color: #d0dbe6 !important;
    }

    /* ===== カスタムクラス ===== */
    .tech-card {
        background: rgba(13, 43, 69, 0.7);
        border: 1px solid rgba(255, 107, 53, 0.2);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }

    .accent-text {
        color: #ff6b35;
        font-weight: 600;
    }

    .muted-text {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.85rem;
    }

    /* フッター */
    .footer-text {
        color: rgba(255, 255, 255, 0.4);
        font-size: 0.8rem;
        text-align: center;
        padding: 2rem 0;
        border-top: 1px solid rgba(255, 107, 53, 0.1);
        margin-top: 2rem;
    }

    /* ===== マルチセレクトのタグ ===== */
    .stMultiSelect [data-baseweb="tag"] {
        background: rgba(255, 107, 53, 0.2) !important;
        border: 1px solid rgba(255, 107, 53, 0.4) !important;
        color: #ffffff !important;
    }

    /* ===== セレクトボックスのドロップダウン ===== */
    [data-baseweb="popover"] {
        background: #0d2b45 !important;
        border: 1px solid rgba(255, 107, 53, 0.3) !important;
    }

    [data-baseweb="menu"] {
        background: #0d2b45 !important;
    }

    [data-baseweb="menu"] li {
        color: #e8eef4 !important;
    }

    [data-baseweb="menu"] li:hover {
        background: rgba(255, 107, 53, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================
# 定数定義
# =====================================

TRAINERS = {
    "岡田": "okada",
    "山本": "yamamoto",
    "板倉": "itakura",
    "葛本": "kuzumoto"
}

LOCATIONS = {
    "島田本町": "shimadahonmachi",
    "伊福町": "ifukucho"
}

# 宣材写真用シチュエーション
SITUATIONS = {
    "カウンセリング・相談": "consultation",
    "姿勢チェック・診断": "posture_check",
    "セッション風景（落ち着いた雰囲気）": "training_session",
    "食事相談・説明": "nutrition_counseling",
    "施設内観（人物なし）": "interior",
    "図解・インフォグラフィック": "infographic",
    "目標達成で喜ぶ風景": "goal_achievement"
}

# SNS投稿タイプ
SNS_POST_TYPES = {
    "Google Map": {
        "月曜：3軸診断の紹介": "3axis_intro",
        "火曜：お客様の成果報告": "customer_success",
        "水曜：施設・設備の紹介": "facility_intro",
        "木曜：トレーナー紹介": "trainer_intro",
        "金曜：よくある質問": "faq",
        "土曜：健康・運動の豆知識": "health_tips",
        "日曜：空き状況・キャンペーン": "availability"
    },
    "Instagram": {
        "教育系：セルフチェック・知識": "education",
        "共感系：悩み→解決": "empathy",
        "信頼系：お客様の声・実績": "trust"
    }
}

# =====================================
# Instagram複数ページ投稿用定義
# =====================================

# 投稿テーマ（大カテゴリ）
INSTAGRAM_THEMES = {
    "ジム継続の悩み": "gym_continuation",
    "ダイエットの悩み": "diet_problem",
    "姿勢改善": "posture_improvement",
    "3軸診断の解説": "3axis_explanation",
    "食事・栄養": "nutrition",
    "運動習慣づくり": "exercise_habit",
    "年代別のお悩み": "age_specific",
    "お客様の声・成果": "customer_voice",
    "トレーナー紹介": "trainer_intro",
    "よくある質問": "faq",
    "施設・設備紹介": "facility",
    "キャンペーン・お知らせ": "campaign"
}

# 見出しテンプレート（テーマごと）
HEADLINE_TEMPLATES = {
    "ジム継続の悩み": [
        "「ジムが続かない」本当の理由",
        "なぜ3ヶ月で挫折するのか",
        "意志が弱いから続かない？",
        "ジム選びで失敗する人の特徴",
        "続けられる人と続けられない人の違い",
        "週1回でも効果は出る？",
        "モチベーションが続かない時の対処法",
        "「忙しい」は言い訳じゃない",
        "完璧主義がジム継続を妨げる",
        "パーソナルと24時間ジムの違い"
    ],
    "ダイエットの悩み": [
        "食べないダイエットが失敗する理由",
        "リバウンドを繰り返す人の共通点",
        "糖質制限は本当に効果的？",
        "40代からのダイエットが難しい理由",
        "痩せたいのに痩せられない本当の原因",
        "体重が減らない停滞期の乗り越え方",
        "「食べてないのに太る」の真実",
        "ダイエット成功に必要な3つのこと",
        "極端な食事制限のリスク",
        "健康的に痩せるペースとは"
    ],
    "姿勢改善": [
        "デスクワークで姿勢が悪くなる理由",
        "猫背を治すと印象が変わる",
        "肩こり・腰痛と姿勢の関係",
        "反り腰チェック方法",
        "巻き肩の原因と改善法",
        "ストレートネックのリスク",
        "姿勢改善で得られる5つのメリット",
        "座り方を変えるだけで変わる",
        "姿勢と自律神経の関係",
        "30秒でできる姿勢チェック"
    ],
    "3軸診断の解説": [
        "3軸診断とは？",
        "姿勢軸：体の土台を整える",
        "食事軸：無理なく続ける食習慣",
        "継続軸：習慣化のメカニズム",
        "なぜ3軸が必要なのか",
        "1軸だけでは効果が出ない理由",
        "3軸診断の流れ",
        "診断結果の見方",
        "あなたに合ったアプローチ",
        "3軸で変わった人の声"
    ],
    "食事・栄養": [
        "タンパク質、足りてますか？",
        "1日に必要なタンパク質量",
        "プロテインは必要？",
        "コンビニで選ぶ高タンパク食",
        "外食でも太らない選び方",
        "お酒とダイエットの関係",
        "間食をやめられない時の対処法",
        "朝食を抜くとどうなる？",
        "水分摂取の重要性",
        "食事記録をつけるメリット"
    ],
    "運動習慣づくり": [
        "運動が苦手でも大丈夫",
        "週何回運動すればいい？",
        "朝と夜、どちらが効果的？",
        "筋トレと有酸素運動の違い",
        "自宅でできる簡単エクササイズ",
        "運動を習慣化するコツ",
        "「時間がない」を解決する方法",
        "運動嫌いが運動好きになるまで",
        "続けやすい運動の選び方",
        "パーソナルトレーニングのメリット"
    ],
    "年代別のお悩み": [
        "30代からの体型変化",
        "40代、代謝が落ちてきた",
        "50代からでも遅くない",
        "産後の体型戻し",
        "更年期と体重の関係",
        "30代男性の健康管理",
        "40代ビジネスマンの運動習慣",
        "シニア世代の筋力維持",
        "年齢に合った運動強度",
        "世代別おすすめトレーニング"
    ],
    "お客様の声・成果": [
        "3ヶ月で-5kg達成",
        "姿勢が変わって肩こり改善",
        "服のサイズが2サイズダウン",
        "体重より見た目が変わった",
        "運動習慣が身についた",
        "食事の意識が変わった",
        "自分に自信が持てるように",
        "周りから「痩せた？」と言われる",
        "健康診断の数値が改善",
        "リバウンドしなくなった"
    ],
    "トレーナー紹介": [
        "トレーナー紹介：岡田",
        "トレーナー紹介：山本",
        "トレーナー紹介：板倉",
        "トレーナー紹介：葛本",
        "私がトレーナーになった理由",
        "得意な指導スタイル",
        "お客様へのメッセージ",
        "トレーナーの1日",
        "資格・経歴紹介",
        "トレーニングへのこだわり"
    ],
    "よくある質問": [
        "Q. どれくらいで効果が出る？",
        "Q. 運動経験がなくても大丈夫？",
        "Q. 食事制限は厳しい？",
        "Q. 週1回でも効果はある？",
        "Q. 予約は取りやすい？",
        "Q. キャンセルはできる？",
        "Q. 持ち物は何が必要？",
        "Q. 無料カウンセリングの内容は？",
        "Q. 料金プランについて",
        "Q. 他のジムとの違いは？"
    ],
    "施設・設備紹介": [
        "完全個室でプライベート空間",
        "最新のトレーニング機器",
        "清潔で快適な空間",
        "シャワー・更衣室完備",
        "駅から徒歩〇分の好立地",
        "駐車場完備で車でも安心",
        "島田本町店のご紹介",
        "伊福町店のご紹介",
        "店内ツアー",
        "こだわりの設備"
    ],
    "キャンペーン・お知らせ": [
        "今週の空き状況",
        "新規入会キャンペーン",
        "期間限定特別プラン",
        "無料カウンセリング受付中",
        "友達紹介キャンペーン",
        "年末年始の営業案内",
        "GW特別プログラム",
        "夏までに変わりたい方へ",
        "新トレーナー加入のお知らせ",
        "営業時間変更のお知らせ"
    ]
}

# サブテキストテンプレート
SUBTEXT_TEMPLATES = {
    "問題提起": [
        "こんな悩みありませんか？",
        "こんな経験ありませんか？",
        "当てはまる方は要注意",
        "心当たりはありませんか？",
        "実は多くの方が悩んでいます"
    ],
    "原因説明": [
        "その原因は...",
        "実は〇〇が原因かも",
        "知っていましたか？",
        "多くの人が知らない事実",
        "専門家が解説します"
    ],
    "解決策提示": [
        "解決策は3つ",
        "ポイントは〇〇",
        "まずはここから始めよう",
        "簡単にできる方法",
        "FIREFITNESSなら解決できます"
    ],
    "メリット訴求": [
        "こんなメリットがあります",
        "〇〇で得られる効果",
        "変化を実感できる",
        "多くの方が効果を実感",
        "始めて良かったの声多数"
    ],
    "行動喚起": [
        "まずは無料カウンセリングへ",
        "お気軽にご相談ください",
        "今すぐ始めませんか？",
        "変わるなら今です",
        "一歩踏み出してみませんか？"
    ],
    "数値・実績": [
        "平均-5kg達成",
        "継続率90%以上",
        "満足度98%",
        "累計〇〇名が体験",
        "3ヶ月で効果を実感"
    ],
    "リスト形式": [
        "①〇〇\n②〇〇\n③〇〇",
        "・ポイント1\n・ポイント2\n・ポイント3",
        "STEP1→STEP2→STEP3",
        "Before → After",
        "原因 → 対策 → 結果"
    ]
}

# アクセントテキストテンプレート
ACCENT_TEMPLATES = [
    "意志の弱さではありません",
    "それ、間違いかもしれません",
    "実は逆効果です",
    "ここが重要ポイント",
    "多くの人が見落としがち",
    "プロが教える秘訣",
    "これが成功の鍵",
    "今すぐチェック",
    "無料カウンセリング受付中",
    "期間限定",
    "先着〇名様限定",
    "お見逃しなく",
    "詳しくはプロフィールから",
    "保存してあとで見返そう",
    "友達にもシェアしてね"
]

# ページタイプ定義（1〜8ページ目）
PAGE_TYPES = {
    1: {
        "name": "タイトルページ",
        "description": "目を引くタイトルで興味を惹く",
        "layouts": ["テキスト中心（シンプル）", "写真メイン＋テキスト"]
    },
    2: {
        "name": "問題提起ページ",
        "description": "読者の悩みに共感する",
        "layouts": ["テキスト中心（シンプル）", "カード型（情報整理）"]
    },
    3: {
        "name": "原因説明ページ",
        "description": "なぜその問題が起きるのか解説",
        "layouts": ["図解・インフォグラフィック", "ステップ・手順説明"]
    },
    4: {
        "name": "解決策ページ",
        "description": "具体的な解決方法を提示",
        "layouts": ["ステップ・手順説明", "図解・インフォグラフィック"]
    },
    5: {
        "name": "詳細説明ページ",
        "description": "ポイントを詳しく解説",
        "layouts": ["カード型（情報整理）", "図解・インフォグラフィック"]
    },
    6: {
        "name": "実績・証拠ページ",
        "description": "お客様の声や数値で信頼性UP",
        "layouts": ["引用・お客様の声", "ビフォーアフター風（数値）"]
    },
    7: {
        "name": "まとめページ",
        "description": "ポイントを簡潔にまとめる",
        "layouts": ["テキスト中心（シンプル）", "カード型（情報整理）"]
    },
    8: {
        "name": "CTA（行動喚起）ページ",
        "description": "次のアクションを促す",
        "layouts": ["テキスト中心（シンプル）", "写真メイン＋テキスト"]
    }
}

# ページ構成プリセット
PAGE_PRESETS = {
    "3ページ構成（シンプル）": [1, 4, 8],
    "4ページ構成（基本）": [1, 2, 4, 8],
    "5ページ構成（標準）": [1, 2, 3, 4, 8],
    "6ページ構成（詳細）": [1, 2, 3, 4, 6, 8],
    "7ページ構成（充実）": [1, 2, 3, 4, 5, 6, 8],
    "8ページ構成（フル）": [1, 2, 3, 4, 5, 6, 7, 8]
}

# アイコンタイプ選択肢
ICON_TYPES = [
    "なし",
    "3軸アイコン（姿勢・食事・継続）",
    "チェックマーク",
    "番号リスト（1,2,3...）",
    "矢印・フロー",
    "人物シルエット",
    "ダンベル・運動器具",
    "フォーク・ナイフ（食事）",
    "時計・カレンダー",
    "グラフ・チャート",
    "星・評価マーク",
    "ハート・健康",
    "脳・メンタル",
    "体のパーツ（筋肉・骨格）",
    "吹き出し・会話",
    "メダル・達成",
    "スマホ・デジタル",
    "ビル・店舗"
]

# フォントスタイル選択肢
FONT_STYLES = [
    "ゴシック体（モダン）",
    "明朝体（上品）",
    "丸ゴシック（親しみやすい）",
    "太ゴシック（力強い）",
    "細ゴシック（洗練）",
    "手書き風（カジュアル）"
]

# 装飾要素選択肢
DECORATION_OPTIONS = [
    "なし",
    "吹き出し",
    "引用符",
    "アンダーライン",
    "背景図形（四角）",
    "背景図形（丸）",
    "枠線",
    "影付き",
    "グラデーション背景",
    "ドット模様",
    "ストライプ模様"
]

# 枠線スタイル選択肢
BORDER_STYLES = [
    "なし",
    "細い枠（ネイビー）",
    "細い枠（オレンジ）",
    "細い枠（白）",
    "太い枠（ネイビー）",
    "太い枠（オレンジ）",
    "角丸枠（ネイビー）",
    "角丸枠（オレンジ）",
    "ダブルライン",
    "点線",
    "破線"
]

# 雰囲気選択肢
MOOD_OPTIONS = [
    "落ち着いた・信頼感",
    "やや落ち着いた",
    "ニュートラル",
    "やや活気ある",
    "活気ある・エネルギッシュ",
    "高級感・プレミアム",
    "親しみやすい・カジュアル",
    "シンプル・ミニマル",
    "情熱的・モチベーション"
]

# 色の強さ選択肢
COLOR_INTENSITY_OPTIONS = [
    "淡い・パステル",
    "やや淡い",
    "標準",
    "やや濃い",
    "濃い・ビビッド"
]

# SNS投稿用レイアウトスタイル
LAYOUT_STYLES = {
    "テキスト中心（シンプル）": "text_centered",
    "図解・インフォグラフィック": "infographic",
    "写真メイン＋テキスト": "photo_with_text",
    "カード型（情報整理）": "card_layout",
    "引用・お客様の声": "testimonial",
    "ステップ・手順説明": "step_by_step",
    "ビフォーアフター風（数値）": "before_after_numbers",
    "Q&A形式": "qa_format"
}

# テキスト配置オプション
TEXT_POSITIONS = {
    "上部": "top",
    "中央": "center",
    "下部": "bottom",
    "左上": "top_left",
    "右上": "top_right",
    "左下": "bottom_left",
    "右下": "bottom_right"
}

# テキストサイズ
TEXT_SIZES = {
    "極小": "xs",
    "小": "small",
    "中": "medium",
    "大": "large",
    "特大": "xl",
    "極大": "xxl"
}

# 背景スタイル
BACKGROUND_STYLES = {
    "単色（白）": {"type": "solid", "color": "#ffffff", "opacity": 100},
    "単色（ダークネイビー）": {"type": "solid", "color": "#0d2b45", "opacity": 100},
    "単色（ライトグレー）": {"type": "solid", "color": "#f5f5f5", "opacity": 100},
    "グラデーション（ネイビー→白）": {"type": "gradient", "colors": ["#0d2b45", "#ffffff"], "opacity": 100},
    "グラデーション（オレンジ→白）": {"type": "gradient", "colors": ["#ff6b35", "#ffffff"], "opacity": 100},
    "写真背景（透明度50%）": {"type": "photo", "color": "#000000", "opacity": 50},
    "写真背景（透明度30%）": {"type": "photo", "color": "#000000", "opacity": 30},
    "写真背景（透明度70%）": {"type": "photo", "color": "#000000", "opacity": 70},
    "写真背景（白オーバーレイ50%）": {"type": "photo", "color": "#ffffff", "opacity": 50},
}

# アスペクト比
ASPECT_RATIOS = {
    "1:1（正方形・Instagram）": "1:1",
    "4:5（縦長・Instagram）": "4:5",
    "9:16（ストーリー・リール）": "9:16",
    "16:9（横長）": "16:9",
    "4:3（Google Map推奨）": "4:3",
    "3:2": "3:2"
}

CLIENT_TYPES = {
    "なし（人物なし）": None,
    "30代女性": "30s_female",
    "30代男性": "30s_male",
    "40代女性": "40s_female",
    "40代男性ビジネスマン": "40s_businessman",
    "50代女性": "50s_female",
    "50代男性": "50s_male",
    "シニア女性（60代以上）": "senior_female",
    "シニア男性（60代以上）": "senior_male",
    "主婦層": "housewife"
}

# ブランドカラー
BRAND_COLORS = {
    "ダークネイビー（メイン）": "#0d2b45",
    "オレンジ（アクセント）": "#ff6b35",
    "白": "#ffffff",
    "ライトグレー": "#f5f5f5",
    "黒": "#000000"
}

# =====================================
# ヘルパー関数
# =====================================

# アセットパス
ASSETS_DIR = Path(__file__).parent / "assets"
TRAINERS_DIR = ASSETS_DIR / "trainers"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
LOGOS_DIR = ASSETS_DIR / "logos"
OUTPUTS_DIR = Path(__file__).parent / "outputs"

# 出力ディレクトリ作成
OUTPUTS_DIR.mkdir(exist_ok=True)

# =====================================
# SVGアイコン定義
# =====================================
ICONS = {
    "fire": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>''',
    "settings": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>''',
    "building": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>''',
    "user": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>''',
    "image": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>''',
    "camera": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>''',
    "share": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>''',
    "sliders": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>''',
    "edit": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>''',
    "type": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>''',
    "palette": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.555C21.965 6.012 17.461 2 12 2z"/></svg>''',
    "layout": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>''',
    "grid": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>''',
    "download": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>''',
    "book": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>''',
    "zap": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>''',
    "check": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>''',
    "sparkles": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></svg>''',
}


def icon(name: str, color: str = "#ff6b35", size: int = 18) -> str:
    """SVGアイコンをHTMLとして返す"""
    svg = ICONS.get(name, "")
    styled_svg = svg.replace('width="18"', f'width="{size}"').replace('height="18"', f'height="{size}"').replace('width="24"', f'width="{size}"').replace('height="24"', f'height="{size}"')
    return f'<span style="display: inline-flex; align-items: center; color: {color}; margin-right: 0.5rem;">{styled_svg}</span>'


def section_header(icon_name: str, title: str, color: str = "#ff6b35") -> None:
    """セクションヘッダーを表示"""
    st.markdown(f'''
    <div style="display: flex; align-items: center; margin-bottom: 0.75rem; margin-top: 0.5rem;">
        {icon(icon_name, color, 20)}
        <span style="color: #ffffff; font-size: 1rem; font-weight: 500; letter-spacing: 0.02em;">{title}</span>
    </div>
    ''', unsafe_allow_html=True)


def get_available_images(directory: Path) -> list:
    """指定ディレクトリ内の画像ファイル一覧を取得"""
    if not directory.exists():
        return []
    extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    return [f for f in directory.iterdir() if f.suffix.lower() in extensions]


def load_image_as_base64(image_path: Path) -> str:
    """画像をbase64エンコード"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# =====================================
# 宣材写真モード
# =====================================

def render_promo_photo_mode():
    """宣材写真生成モードのUI"""

    # サイドバー：設定
    with st.sidebar:
        section_header("settings", "基本設定")

        # 店舗選択
        section_header("building", "店舗（背景）")
        selected_location = st.selectbox(
            "店舗を選択",
            options=list(LOCATIONS.keys()),
            help="選択した店舗の背景画像が使用されます",
            key="promo_location"
        )

        # 背景画像選択
        bg_dir = BACKGROUNDS_DIR / LOCATIONS[selected_location]
        bg_images = get_available_images(bg_dir)

        if bg_images:
            selected_bg = st.selectbox(
                "背景画像を選択",
                options=bg_images,
                format_func=lambda x: x.name,
                key="promo_bg"
            )
            st.image(str(selected_bg), caption="選択中の背景", use_container_width=True)
        else:
            st.warning(f"背景画像がありません: {bg_dir}")
            selected_bg = None

        st.divider()

        # トレーナー選択
        section_header("user", "トレーナー")
        use_trainer = st.checkbox("トレーナーを登場させる", value=True, key="promo_use_trainer")

        selected_trainer = None
        selected_trainer_name = None

        if use_trainer:
            selected_trainer_name = st.selectbox(
                "トレーナーを選択",
                options=list(TRAINERS.keys()),
                key="promo_trainer"
            )

            trainer_dir = TRAINERS_DIR / TRAINERS[selected_trainer_name]
            trainer_images = get_available_images(trainer_dir)

            if trainer_images:
                selected_trainer = st.multiselect(
                    "参照画像を選択（複数可）",
                    options=trainer_images,
                    format_func=lambda x: x.name,
                    default=[trainer_images[0]] if trainer_images else [],
                    key="promo_trainer_images"
                )

                if selected_trainer:
                    cols = st.columns(min(len(selected_trainer), 2))
                    for i, img in enumerate(selected_trainer[:2]):
                        with cols[i]:
                            st.image(str(img), caption=img.name, use_container_width=True)
            else:
                st.warning(f"トレーナー画像がありません: {trainer_dir}")

    # メインエリア
    col1, col2 = st.columns([1, 1])

    with col1:
        section_header("image", "画像設定")

        # シチュエーション
        selected_situation = st.selectbox(
            "シチュエーション",
            options=list(SITUATIONS.keys()),
            help="生成する画像のシーン",
            key="promo_situation"
        )

        # クライアント（登場人物）
        selected_client = st.selectbox(
            "クライアント（登場人物）",
            options=list(CLIENT_TYPES.keys()),
            help="トレーナーと一緒に登場する人物",
            key="promo_client"
        )

        # アスペクト比
        selected_ratio = st.selectbox(
            "アスペクト比",
            options=list(ASPECT_RATIOS.keys()),
            key="promo_ratio"
        )

        st.divider()

        # 追加指示
        section_header("edit", "追加の指示")
        additional_prompt = st.text_area(
            "生成したい画像の詳細を日本語で入力",
            placeholder="例：笑顔で会話している様子、窓から自然光が入っている、清潔感のある雰囲気",
            height=100,
            key="promo_additional"
        )

        # 詳細オプション
        with st.expander("詳細オプション"):
            include_text = st.checkbox("画像内にテキストを含める", value=False, key="promo_include_text")
            if include_text:
                image_text = st.text_input(
                    "画像内に入れるテキスト",
                    placeholder="例：3軸診断、無料カウンセリング",
                    key="promo_image_text"
                )
            else:
                image_text = None

            mood = st.select_slider(
                "雰囲気",
                options=["落ち着いた", "やや落ち着いた", "ニュートラル", "やや活気ある", "活気ある"],
                value="やや落ち着いた",
                key="promo_mood"
            )

    with col2:
        section_header("sparkles", "生成プレビュー")

        # 入力情報のサマリー
        summary_parts = []
        summary_parts.append(f"**店舗**: {selected_location}")
        summary_parts.append(f"**シチュエーション**: {selected_situation}")
        if use_trainer and selected_trainer:
            summary_parts.append(f"**トレーナー**: {selected_trainer_name}")
        if CLIENT_TYPES[selected_client]:
            summary_parts.append(f"**クライアント**: {selected_client}")
        summary_parts.append(f"**アスペクト比**: {selected_ratio}")

        st.info("\n\n".join(summary_parts))

        if additional_prompt:
            st.write("**追加指示:**")
            st.write(additional_prompt)

    st.divider()

    # 生成ボタン
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_button = st.button(
            "Generate Image",
            use_container_width=True,
            type="primary",
            key="promo_generate"
        )

    # 生成処理
    if generate_button:
        run_generation(
            mode="promo",
            location=selected_location,
            situation=selected_situation,
            trainer_name=selected_trainer_name if use_trainer else None,
            trainer_images=selected_trainer if use_trainer else [],
            client=selected_client,
            aspect_ratio=ASPECT_RATIOS[selected_ratio],
            additional_prompt=additional_prompt,
            image_text=image_text if include_text else None,
            mood=mood,
            selected_bg=selected_bg
        )


# =====================================
# SNS投稿モード
# =====================================

def render_sns_post_mode():
    """SNS投稿画像生成モードのUI"""

    st.markdown(f'''
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
        {icon("share", "#ff6b35", 22)}
        <span style="color: #ffffff; font-size: 1.1rem; font-weight: 500;">SNS投稿用画像を選択肢から設定して生成</span>
    </div>
    ''', unsafe_allow_html=True)

    # サイドバー
    with st.sidebar:
        section_header("sliders", "SNS投稿設定")

        # プラットフォーム選択
        platform = st.radio(
            "投稿先プラットフォーム",
            options=["Google Map", "Instagram（単体）", "Instagram（複数ページ）"],
            key="sns_platform"
        )

        # Instagram複数ページモードの場合
        if platform == "Instagram（複数ページ）":
            st.divider()
            section_header("grid", "ページ構成")

            # ページ構成プリセット
            page_preset = st.selectbox(
                "ページ構成",
                options=list(PAGE_PRESETS.keys()),
                index=2,  # 5ページ構成がデフォルト
                key="sns_page_preset"
            )

            # 選択されたページ
            selected_pages = PAGE_PRESETS[page_preset]
            st.info(f"生成ページ: {len(selected_pages)}ページ")

            # テーマ選択
            selected_theme = st.selectbox(
                "投稿テーマ",
                options=list(INSTAGRAM_THEMES.keys()),
                key="sns_theme"
            )
        else:
            # 通常モード
            if platform == "Google Map":
                post_types = SNS_POST_TYPES["Google Map"]
            else:
                post_types = SNS_POST_TYPES["Instagram"]

            selected_post_type = st.selectbox(
                "投稿タイプ",
                options=list(post_types.keys()),
                key="sns_post_type"
            )

        st.divider()

        # ロゴ設定
        section_header("fire", "FIREFITNESSロゴ")
        include_logo = st.checkbox("ロゴを必ず含める", value=True, key="sns_include_logo")

        if include_logo:
            logo_position = st.selectbox(
                "ロゴの位置",
                options=list(TEXT_POSITIONS.keys()),
                index=6,  # 右下デフォルト
                key="sns_logo_position"
            )
            logo_size = st.selectbox(
                "ロゴサイズ",
                options=list(TEXT_SIZES.keys()),
                index=2,  # 中デフォルト
                key="sns_logo_size"
            )

        st.divider()

        # トレーナー写真
        section_header("user", "トレーナー写真")
        include_trainer_photo = st.checkbox("トレーナー写真を含める", value=False, key="sns_include_trainer")

        selected_trainer = None
        selected_trainer_name = None
        trainer_photo_style = None

        if include_trainer_photo:
            selected_trainer_name = st.selectbox(
                "トレーナーを選択",
                options=list(TRAINERS.keys()),
                key="sns_trainer"
            )

            trainer_dir = TRAINERS_DIR / TRAINERS[selected_trainer_name]
            trainer_images = get_available_images(trainer_dir)

            if trainer_images:
                selected_trainer = st.multiselect(
                    "参照画像を選択",
                    options=trainer_images,
                    format_func=lambda x: x.name,
                    default=[trainer_images[0]] if trainer_images else [],
                    key="sns_trainer_images"
                )

                trainer_photo_style = st.selectbox(
                    "トレーナー写真のスタイル",
                    options=["円形切り抜き", "四角形", "全身", "上半身のみ"],
                    key="sns_trainer_style"
                )

    # ====================================
    # Instagram複数ページモード
    # ====================================
    if platform == "Instagram（複数ページ）":
        render_instagram_multipage_mode(
            selected_theme=selected_theme,
            selected_pages=selected_pages,
            include_logo=include_logo,
            logo_position=logo_position if include_logo else None,
            logo_size=logo_size if include_logo else None,
            include_trainer_photo=include_trainer_photo,
            selected_trainer_name=selected_trainer_name,
            selected_trainer=selected_trainer,
            trainer_photo_style=trainer_photo_style
        )
        return

    # ====================================
    # 通常モード（単体画像）
    # ====================================
    # メインエリア - 2カラム
    col1, col2 = st.columns([1, 1])

    with col1:
        section_header("type", "テキスト設定")

        # テーマから見出しを選択（Instagram単体の場合）
        if platform == "Instagram（単体）":
            # テーマ選択
            headline_theme = st.selectbox(
                "見出しテーマ",
                options=list(HEADLINE_TEMPLATES.keys()),
                key="sns_headline_theme"
            )

            # 見出し選択
            main_headline = st.selectbox(
                "見出しテキスト",
                options=HEADLINE_TEMPLATES[headline_theme],
                key="sns_headline"
            )
        else:
            # Google Mapの場合はテンプレートから選択
            gmap_headlines = {
                "月曜：3軸診断の紹介": ["3軸診断とは", "姿勢・食事・継続の3軸", "あなたに合ったアプローチ"],
                "火曜：お客様の成果報告": ["3ヶ月で-5kg達成", "姿勢改善で肩こり解消", "運動習慣が身についた"],
                "水曜：施設・設備の紹介": ["完全個室でプライベート", "最新トレーニング機器", "清潔で快適な空間"],
                "木曜：トレーナー紹介": ["トレーナー紹介", "私がトレーナーになった理由", "お客様へのメッセージ"],
                "金曜：よくある質問": ["Q. どれくらいで効果が出る？", "Q. 運動経験がなくても大丈夫？", "Q. 食事制限は厳しい？"],
                "土曜：健康・運動の豆知識": ["知ってましたか？", "タンパク質足りてますか？", "姿勢と健康の関係"],
                "日曜：空き状況・キャンペーン": ["今週の空き状況", "無料カウンセリング受付中", "新規入会キャンペーン"]
            }
            headlines = gmap_headlines.get(selected_post_type, ["テキストを選択"])
            main_headline = st.selectbox(
                "見出しテキスト",
                options=headlines,
                key="sns_headline"
            )

        headline_color = st.selectbox(
            "見出しの色",
            options=list(BRAND_COLORS.keys()),
            key="sns_headline_color"
        )

        headline_size = st.selectbox(
            "見出しサイズ",
            options=list(TEXT_SIZES.keys()),
            index=3,  # 大デフォルト
            key="sns_headline_size"
        )

        headline_position = st.selectbox(
            "見出しの位置",
            options=list(TEXT_POSITIONS.keys()),
            index=1,  # 中央デフォルト
            key="sns_headline_position"
        )

        st.divider()

        # サブテキスト
        st.markdown('<p style="color: #b8c9d9; font-size: 0.9rem; margin-bottom: 0.5rem;">サブテキスト</p>', unsafe_allow_html=True)

        subtext_category = st.selectbox(
            "サブテキストのカテゴリ",
            options=["なし"] + list(SUBTEXT_TEMPLATES.keys()),
            key="sns_subtext_category"
        )

        if subtext_category != "なし":
            sub_text = st.selectbox(
                "サブテキスト",
                options=SUBTEXT_TEMPLATES[subtext_category],
                key="sns_subtext"
            )

            subtext_color = st.selectbox(
                "サブテキストの色",
                options=list(BRAND_COLORS.keys()),
                index=0,  # ネイビーデフォルト
                key="sns_subtext_color"
            )

            subtext_size = st.selectbox(
                "サブテキストサイズ",
                options=list(TEXT_SIZES.keys()),
                index=2,  # 中デフォルト
                key="sns_subtext_size"
            )
        else:
            sub_text = ""

        st.divider()

        # アクセントテキスト
        st.markdown('<p style="color: #b8c9d9; font-size: 0.9rem; margin-bottom: 0.5rem;">アクセント</p>', unsafe_allow_html=True)

        accent_text = st.selectbox(
            "アクセントテキスト",
            options=["なし"] + ACCENT_TEMPLATES,
            key="sns_accent"
        )

        if accent_text != "なし":
            accent_style = st.selectbox(
                "アクセントスタイル",
                options=["アンダーライン（オレンジ）", "背景色（オレンジ）", "背景色（ネイビー）", "太字のみ"],
                key="sns_accent_style"
            )
        else:
            accent_style = None

    with col2:
        section_header("palette", "デザイン設定")

        # レイアウトスタイル
        st.markdown('<p style="color: #b8c9d9; font-size: 0.9rem; margin-bottom: 0.5rem;">レイアウト</p>', unsafe_allow_html=True)
        layout_style = st.selectbox(
            "レイアウトスタイル",
            options=list(LAYOUT_STYLES.keys()),
            key="sns_layout"
        )

        st.divider()

        # 背景設定
        st.markdown('<p style="color: #b8c9d9; font-size: 0.9rem; margin-bottom: 0.5rem;">背景</p>', unsafe_allow_html=True)
        background_style = st.selectbox(
            "背景スタイル",
            options=list(BACKGROUND_STYLES.keys()),
            key="sns_bg_style"
        )

        # 写真背景の場合
        if "写真背景" in background_style:
            st.info("写真背景を使用する場合、下で背景画像を選択してください")

            selected_location = st.selectbox(
                "店舗を選択",
                options=list(LOCATIONS.keys()),
                key="sns_location"
            )

            bg_dir = BACKGROUNDS_DIR / LOCATIONS[selected_location]
            bg_images = get_available_images(bg_dir)

            if bg_images:
                selected_bg = st.selectbox(
                    "背景画像を選択",
                    options=bg_images,
                    format_func=lambda x: x.name,
                    key="sns_bg_image"
                )
                st.image(str(selected_bg), caption="選択中の背景", use_container_width=True)
            else:
                selected_bg = None
        else:
            selected_bg = None
            selected_location = None

        # カスタム透明度
        if "写真背景" in background_style:
            custom_opacity = st.slider(
                "背景透明度をカスタマイズ",
                min_value=0,
                max_value=100,
                value=BACKGROUND_STYLES[background_style]["opacity"],
                key="sns_custom_opacity"
            )
        else:
            custom_opacity = 100

        st.divider()

        # 図解・アイコン設定
        st.markdown('<p style="color: #b8c9d9; font-size: 0.9rem; margin-bottom: 0.5rem;">図解・アイコン</p>', unsafe_allow_html=True)
        icon_type = st.selectbox(
            "アイコンタイプ",
            options=ICON_TYPES,
            key="sns_icon_type"
        )
        include_icons = icon_type != "なし"

        st.divider()

        # アスペクト比
        st.markdown('<p style="color: #b8c9d9; font-size: 0.9rem; margin-bottom: 0.5rem;">サイズ</p>', unsafe_allow_html=True)
        selected_ratio = st.selectbox(
            "アスペクト比",
            options=list(ASPECT_RATIOS.keys()),
            index=0 if platform == "Instagram（単体）" else 4,  # Insta: 1:1, Google Map: 4:3
            key="sns_ratio"
        )

    st.divider()

    # 詳細設定（折りたたみ）
    with st.expander("さらに詳細な設定"):
        detail_col1, detail_col2, detail_col3 = st.columns(3)

        with detail_col1:
            st.markdown('<p style="color: #ffffff; font-size: 0.95rem; font-weight: 500; margin-bottom: 0.5rem;">フォント設定</p>', unsafe_allow_html=True)
            font_style = st.selectbox(
                "フォントスタイル",
                options=FONT_STYLES,
                key="sns_font_style"
            )

            text_shadow = st.selectbox(
                "テキストの影",
                options=["なし", "軽い影", "強い影"],
                key="sns_text_shadow"
            )

        with detail_col2:
            st.markdown('<p style="color: #ffffff; font-size: 0.95rem; font-weight: 500; margin-bottom: 0.5rem;">装飾設定</p>', unsafe_allow_html=True)
            border_style = st.selectbox(
                "枠線スタイル",
                options=BORDER_STYLES,
                key="sns_border"
            )

            decoration = st.selectbox(
                "装飾要素",
                options=DECORATION_OPTIONS,
                key="sns_decoration"
            )

        with detail_col3:
            st.markdown('<p style="color: #ffffff; font-size: 0.95rem; font-weight: 500; margin-bottom: 0.5rem;">雰囲気設定</p>', unsafe_allow_html=True)
            overall_mood = st.selectbox(
                "全体の雰囲気",
                options=MOOD_OPTIONS,
                index=1,  # やや落ち着いた
                key="sns_mood"
            )

            color_intensity = st.selectbox(
                "色の強さ",
                options=COLOR_INTENSITY_OPTIONS,
                index=2,  # 標準
                key="sns_color_intensity"
            )

    st.divider()

    # プレビューと生成
    section_header("grid", "設定プレビュー")

    preview_col1, preview_col2 = st.columns([2, 1])

    with preview_col1:
        # 設定サマリー
        st.markdown("#### 現在の設定")

        preview_text = f"""
**プラットフォーム**: {platform}
**投稿タイプ**: {selected_post_type}
**レイアウト**: {layout_style}
**背景**: {background_style}
"""
        if main_headline:
            preview_text += f"\n**見出し**: {main_headline}"
        if sub_text:
            preview_text += f"\n**サブテキスト**: {sub_text[:50]}..."
        if include_logo:
            preview_text += f"\n**ロゴ**: {logo_position}に配置"
        if include_trainer_photo and selected_trainer_name:
            preview_text += f"\n**トレーナー**: {selected_trainer_name}"
        if include_icons:
            preview_text += f"\n**図解**: {icon_type}"

        st.info(preview_text)

    with preview_col2:
        st.markdown("#### クイックテンプレート")

        if st.button("マニュアルのプリセットを適用", key="apply_preset"):
            st.session_state["show_presets"] = True

    # プリセット表示
    if st.session_state.get("show_presets", False):
        render_preset_selector(platform, selected_post_type)

    # 生成ボタン
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_button = st.button(
            "SNS投稿画像を生成する",
            use_container_width=True,
            type="primary",
            key="sns_generate"
        )

    # 生成処理
    if generate_button:
        # SNS投稿用のパラメータを収集
        sns_params = {
            "platform": platform,
            "post_type": selected_post_type if platform != "Instagram（複数ページ）" else "Instagram複数ページ",
            "layout_style": layout_style,
            "background_style": background_style,
            "custom_opacity": custom_opacity if "写真背景" in background_style else 100,
            "main_headline": main_headline,
            "headline_color": BRAND_COLORS[headline_color],
            "headline_size": TEXT_SIZES[headline_size],
            "headline_position": TEXT_POSITIONS[headline_position],
            "sub_text": sub_text if sub_text else "",
            "sub_text_color": BRAND_COLORS.get(subtext_color, "#0d2b45") if subtext_category != "なし" else None,
            "sub_text_size": TEXT_SIZES.get(subtext_size, "medium") if subtext_category != "なし" else None,
            "accent_text": accent_text if accent_text != "なし" else "",
            "accent_style": accent_style if accent_text != "なし" else None,
            "include_logo": include_logo,
            "logo_position": TEXT_POSITIONS.get(logo_position) if include_logo else None,
            "logo_size": TEXT_SIZES.get(logo_size) if include_logo else None,
            "include_trainer_photo": include_trainer_photo,
            "trainer_photo_style": trainer_photo_style if include_trainer_photo else None,
            "include_icons": include_icons,
            "icon_type": icon_type if include_icons else None,
            "font_style": font_style,
            "text_shadow": text_shadow,
            "border_style": border_style,
            "decoration": decoration,
            "overall_mood": overall_mood,
            "color_intensity": color_intensity
        }

        run_sns_generation(
            sns_params=sns_params,
            aspect_ratio=ASPECT_RATIOS[selected_ratio],
            trainer_name=selected_trainer_name if include_trainer_photo else None,
            trainer_images=selected_trainer if include_trainer_photo else [],
            selected_bg=selected_bg
        )


def render_preset_selector(platform: str, post_type: str):
    """マニュアルベースのプリセット選択UI"""

    st.markdown("---")
    st.markdown("#### マニュアルのプリセット")

    # プリセット定義（マニュアルから抽出）
    presets = {
        "Google Map": {
            "月曜：3軸診断の紹介": {
                "headline": "3軸診断",
                "sub_text": "① 姿勢軸\n② 食事軸\n③ 継続軸",
                "layout": "図解・インフォグラフィック",
                "icons": "3軸アイコン（姿勢・食事・継続）"
            },
            "火曜：お客様の成果報告": {
                "headline": "-5kg / 3ヶ月",
                "sub_text": "お客様の成果報告",
                "layout": "テキスト中心（シンプル）",
                "icons": None
            },
            "水曜：施設・設備の紹介": {
                "headline": "完全個室",
                "sub_text": "プライベート空間でマンツーマン",
                "layout": "写真メイン＋テキスト",
                "icons": None
            },
            "木曜：トレーナー紹介": {
                "headline": "トレーナー紹介",
                "sub_text": "",
                "layout": "写真メイン＋テキスト",
                "icons": None
            },
            "金曜：よくある質問": {
                "headline": "Q.",
                "sub_text": "よくある質問にお答えします",
                "layout": "Q&A形式",
                "icons": None
            },
            "土曜：健康・運動の豆知識": {
                "headline": "知ってましたか？",
                "sub_text": "",
                "layout": "図解・インフォグラフィック",
                "icons": "チェックマーク"
            },
            "日曜：空き状況・キャンペーン": {
                "headline": "今週の空き状況",
                "sub_text": "",
                "layout": "カード型（情報整理）",
                "icons": None
            }
        },
        "Instagram": {
            "教育系：セルフチェック・知識": {
                "headline": "",
                "sub_text": "",
                "layout": "ステップ・手順説明",
                "icons": "番号リスト（1,2,3...）"
            },
            "共感系：悩み→解決": {
                "headline": "「ジムが続かない」本当の理由",
                "sub_text": "意志の弱さではありません",
                "layout": "テキスト中心（シンプル）",
                "icons": None
            },
            "信頼系：お客様の声・実績": {
                "headline": "",
                "sub_text": "",
                "layout": "引用・お客様の声",
                "icons": None
            }
        }
    }

    if platform in presets and post_type in presets[platform]:
        preset = presets[platform][post_type]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**見出し**: {preset['headline']}")
            st.markdown(f"**サブテキスト**: {preset['sub_text'][:30]}..." if preset['sub_text'] else "")
        with col2:
            st.markdown(f"**レイアウト**: {preset['layout']}")
            st.markdown(f"**アイコン**: {preset['icons']}" if preset['icons'] else "")

        if st.button("このプリセットを適用", key="apply_this_preset"):
            st.session_state["sns_headline"] = preset["headline"]
            st.session_state["sns_subtext"] = preset["sub_text"]
            st.session_state["sns_layout"] = preset["layout"]
            if preset["icons"]:
                st.session_state["sns_include_icons"] = True
                st.session_state["sns_icon_type"] = preset["icons"]
            st.session_state["show_presets"] = False
            st.rerun()


# =====================================
# Instagram複数ページモード
# =====================================

def render_instagram_multipage_mode(
    selected_theme: str,
    selected_pages: list,
    include_logo: bool,
    logo_position: str,
    logo_size: str,
    include_trainer_photo: bool,
    selected_trainer_name: str,
    selected_trainer: list,
    trainer_photo_style: str
):
    """Instagram複数ページ投稿画像生成モードのUI（AI自動生成版）"""

    section_header("grid", f"Instagram複数ページ投稿 - {selected_theme}")

    # AI生成モードの説明
    st.markdown("""
    <div style="background: rgba(255, 107, 53, 0.1); border: 1px solid rgba(255, 107, 53, 0.3);
                border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <p style="color: #ff6b35; font-weight: 600; margin-bottom: 0.5rem;">
            AI自動生成モード
        </p>
        <p style="color: #d0dbe6; font-size: 0.9rem; margin: 0;">
            テーマを選択するだけで、FIREFITNESSの価値基準（3軸診断：姿勢・食事・継続）に基づいた
            <strong>毎回新しいコンテンツ</strong>をAIが自動生成します。
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"テーマ「{selected_theme}」で {len(selected_pages)}ページの画像を一括生成します")

    # ページ構成の表示
    st.markdown("#### ページ構成（自動生成）")

    # ページタイプをキーに変換するマッピング
    PAGE_TYPE_KEYS = {
        1: "title",
        2: "problem",
        3: "cause",
        4: "solution",
        5: "detail",
        6: "evidence",
        7: "summary",
        8: "cta"
    }

    # ページの概要を表示
    for i, page_num in enumerate(selected_pages):
        page_info = PAGE_TYPES[page_num]
        with st.expander(f"ページ {i+1}: {page_info['name']}", expanded=False):
            st.markdown(f"*{page_info['description']}*")
            st.markdown(f"**推奨レイアウト**: {', '.join(page_info['layouts'])}")
            st.markdown("*見出し・サブテキストはAIが自動生成します*")

    st.divider()

    # 共通設定
    section_header("palette", "共通デザイン設定")

    common_col1, common_col2, common_col3 = st.columns(3)

    with common_col1:
        common_font = st.selectbox(
            "フォントスタイル（共通）",
            options=FONT_STYLES,
            key="mp_common_font"
        )

        common_headline_color = st.selectbox(
            "見出しの色（共通）",
            options=list(BRAND_COLORS.keys()),
            key="mp_common_headline_color"
        )

    with common_col2:
        common_mood = st.selectbox(
            "雰囲気（共通）",
            options=MOOD_OPTIONS,
            index=1,
            key="mp_common_mood"
        )

        common_border = st.selectbox(
            "枠線（共通）",
            options=BORDER_STYLES,
            key="mp_common_border"
        )

    with common_col3:
        common_color_intensity = st.selectbox(
            "色の強さ（共通）",
            options=COLOR_INTENSITY_OPTIONS,
            index=2,
            key="mp_common_color_intensity"
        )

        # 写真背景を使う場合
        use_photo_bg = st.checkbox("写真背景を使用するページあり", key="mp_use_photo_bg")

        if use_photo_bg:
            selected_location = st.selectbox(
                "店舗を選択",
                options=list(LOCATIONS.keys()),
                key="mp_location"
            )

            bg_dir = BACKGROUNDS_DIR / LOCATIONS[selected_location]
            bg_images = get_available_images(bg_dir)

            if bg_images:
                selected_bg = st.selectbox(
                    "背景画像を選択",
                    options=bg_images,
                    format_func=lambda x: x.name,
                    key="mp_bg_image"
                )
            else:
                selected_bg = None
        else:
            selected_bg = None

    st.divider()

    # 生成ボタン
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_all_button = st.button(
            f"AI自動生成で{len(selected_pages)}ページ一括生成",
            use_container_width=True,
            type="primary",
            key="mp_generate_all"
        )

    # 生成処理
    if generate_all_button:
        st.info(f"AIがテーマ「{selected_theme}」に基づいてコンテンツを自動生成し、{len(selected_pages)}ページの画像を作成します...")

        generated_images = []
        generated_contents = []  # 一貫性のため生成済みコンテンツを保存
        progress_bar = st.progress(0)

        for idx, page_num in enumerate(selected_pages):
            page_info = PAGE_TYPES[page_num]
            page_type_key = PAGE_TYPE_KEYS[page_num]

            st.markdown(f"---\n#### ページ {idx+1}: {page_info['name']}")

            # AIでコンテンツを生成
            with st.spinner(f"ページ {idx+1} のコンテンツをAI生成中..."):
                ai_content = generate_sns_content_with_claude(
                    theme=selected_theme,
                    page_type=page_type_key,
                    page_number=idx + 1,
                    total_pages=len(selected_pages),
                    previous_content=generated_contents
                )

                # 生成されたコンテンツを保存
                ai_content["page_type"] = page_type_key
                generated_contents.append(ai_content)

                # 生成されたコンテンツを表示
                with st.expander("AIが生成したコンテンツ", expanded=True):
                    st.markdown(f"**見出し**: {ai_content.get('headline', '')}")
                    st.markdown(f"**サブテキスト**: {ai_content.get('sub_text', '')}")
                    if ai_content.get('body_points'):
                        st.markdown("**ポイント**:")
                        for point in ai_content['body_points']:
                            st.markdown(f"- {point}")
                    if ai_content.get('cta_text'):
                        st.markdown(f"**CTA**: {ai_content.get('cta_text', '')}")

            # 推奨レイアウトを使用
            layout_suggestion = ai_content.get("layout_suggestion", "text_centered")
            layout_style = next(
                (k for k, v in LAYOUT_STYLES.items() if v == layout_suggestion),
                page_info["layouts"][0]  # デフォルトは最初の推奨レイアウト
            )

            # 背景スタイル決定（タイトルページと CTAは写真背景可、他は単色系）
            if page_num in [1, 8] and use_photo_bg and selected_bg:
                bg_style = "写真背景（透明度50%）"
            else:
                bg_style = "単色（白）"

            # 各ページのパラメータを構築
            sns_params = {
                "platform": "Instagram",
                "post_type": f"{selected_theme} - {page_info['name']}",
                "layout_style": layout_style,
                "background_style": bg_style,
                "custom_opacity": BACKGROUND_STYLES[bg_style].get("opacity", 100),
                "main_headline": ai_content.get("headline", ""),
                "headline_color": BRAND_COLORS[common_headline_color],
                "headline_size": TEXT_SIZES["大"],
                "headline_position": TEXT_POSITIONS["中央"],
                "sub_text": ai_content.get("sub_text", ""),
                "sub_text_color": BRAND_COLORS["ダークネイビー（メイン）"],
                "sub_text_size": TEXT_SIZES["中"],
                "accent_text": ai_content.get("accent_text", ""),
                "accent_style": "アンダーライン（オレンジ）" if ai_content.get("accent_text") else None,
                "include_logo": include_logo,
                "logo_position": TEXT_POSITIONS.get(logo_position) if include_logo else None,
                "logo_size": TEXT_SIZES.get(logo_size) if include_logo else None,
                "include_trainer_photo": include_trainer_photo and idx == 0,  # 最初のページのみ
                "trainer_photo_style": trainer_photo_style if include_trainer_photo else None,
                "include_icons": ai_content.get("icon_suggestion", "なし") != "なし",
                "icon_type": ai_content.get("icon_suggestion"),
                "font_style": common_font,
                "text_shadow": "なし",
                "border_style": common_border,
                "decoration": "なし",
                "overall_mood": common_mood,
                "color_intensity": common_color_intensity,
                "page_number": idx + 1,
                "total_pages": len(selected_pages),
                "theme": selected_theme,
                "body_points": ai_content.get("body_points", []),
                "cta_text": ai_content.get("cta_text", "")
            }

            # 参照画像収集
            reference_images = []

            if "写真背景" in bg_style and selected_bg:
                reference_images.append({
                    "path": selected_bg,
                    "type": "background",
                    "description": "店舗背景"
                })

            if include_trainer_photo and selected_trainer and idx == 0:
                for img in selected_trainer:
                    reference_images.append({
                        "path": img,
                        "type": "trainer",
                        "description": f"トレーナー{selected_trainer_name}"
                    })

            # 画像生成
            with st.spinner(f"ページ {idx+1} の画像を生成中..."):
                try:
                    optimized_prompt = convert_sns_prompt_with_claude(sns_params)

                    result = generate_image_with_gemini(
                        prompt=optimized_prompt,
                        reference_images=reference_images,
                        aspect_ratio="1:1",
                        resolution="high"
                    )

                    if result["success"]:
                        st.success(f"ページ {idx+1} 完了")
                        st.image(result["image_path"], caption=f"ページ {idx+1}: {ai_content.get('headline', '')}", use_container_width=True)
                        generated_images.append(result["image_path"])

                        with open(result["image_path"], "rb") as f:
                            st.download_button(
                                label=f"ページ {idx+1} をダウンロード",
                                data=f,
                                file_name=f"firefitness_instagram_{selected_theme.replace('/', '_')}_page{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png",
                                key=f"download_page_{idx}"
                            )
                    else:
                        st.error(f"ページ {idx+1} の生成に失敗: {result.get('error', '不明なエラー')}")

                except Exception as e:
                    st.error(f"ページ {idx+1} でエラー: {str(e)}")
                    import traceback
                    traceback.print_exc()

            progress_bar.progress((idx + 1) / len(selected_pages))

        if generated_images:
            st.success(f"全 {len(generated_images)} ページの生成が完了しました")

            # 生成されたコンテンツのまとめを表示
            st.markdown("---")
            st.markdown("#### 生成されたコンテンツまとめ")
            for i, content in enumerate(generated_contents):
                st.markdown(f"**ページ {i+1}**: {content.get('headline', '')} - {content.get('sub_text', '')}")

            # ハッシュタグ
            st.markdown("---")
            st.markdown("#### 投稿のヒント")
            st.info("""
**共通ハッシュタグ（コピペ用）:**

#岡山パーソナルジム #岡山ダイエット #FIREFITNESS #3軸診断 #パーソナルトレーニング #岡山市 #ダイエット #姿勢改善 #岡山ジム
            """)


# =====================================
# 生成処理
# =====================================

def run_generation(mode, location, situation, trainer_name, trainer_images, client,
                   aspect_ratio, additional_prompt, image_text, mood, selected_bg):
    """宣材写真の生成処理"""

    print("=" * 50)
    print("🔥 生成ボタンが押されました")
    print("=" * 50)
    st.info("処理を開始します...")

    # 入力データ収集
    generation_input = {
        "location": location,
        "situation": situation,
        "trainer": trainer_name,
        "client": client if CLIENT_TYPES.get(client) else None,
        "aspect_ratio": aspect_ratio,
        "resolution": "high",
        "additional_prompt": additional_prompt,
        "image_text": image_text,
        "mood": mood
    }

    # 参照画像収集
    reference_images = []

    # 背景画像
    if selected_bg:
        reference_images.append({
            "path": selected_bg,
            "type": "background",
            "description": f"{location}の店舗背景"
        })

    # トレーナー画像
    if trainer_name and trainer_images:
        for img in trainer_images:
            reference_images.append({
                "path": img,
                "type": "trainer",
                "description": f"トレーナー{trainer_name}"
            })

    with st.spinner("プロンプトを最適化中..."):
        try:
            print("📝 Claude APIを呼び出し中...")
            optimized_prompt = convert_prompt_with_claude(generation_input)
            print(f"✅ プロンプト生成完了: {optimized_prompt[:100]}...")

            with st.expander("最適化されたプロンプト（確認用）"):
                st.code(optimized_prompt, language="text")

        except Exception as e:
            print(f"❌ Claude APIエラー: {str(e)}")
            st.error(f"プロンプト変換エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return

    with st.spinner("画像を生成中... (30秒〜1分程度かかります)"):
        try:
            print("🎨 Gemini APIを呼び出し中...")
            result = generate_image_with_gemini(
                prompt=optimized_prompt,
                reference_images=reference_images,
                aspect_ratio=aspect_ratio,
                resolution="high"
            )

            if result["success"]:
                st.success("画像生成が完了しました")

                st.image(result["image_path"], caption="生成された画像", use_container_width=True)

                with open(result["image_path"], "rb") as f:
                    st.download_button(
                        label="画像をダウンロード",
                        data=f,
                        file_name=f"firefitness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png"
                    )

                if result.get("text_response"):
                    with st.expander("Geminiからのコメント"):
                        st.write(result["text_response"])
            else:
                st.error(f"画像生成エラー: {result.get('error', '不明なエラー')}")

        except Exception as e:
            st.error(f"画像生成エラー: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


def run_sns_generation(sns_params, aspect_ratio, trainer_name, trainer_images, selected_bg):
    """SNS投稿画像の生成処理"""

    print("=" * 50)
    print("📱 SNS投稿画像生成開始")
    print("=" * 50)
    st.info("SNS投稿画像を生成中...")

    # 参照画像収集
    reference_images = []

    # 背景画像
    if selected_bg:
        reference_images.append({
            "path": selected_bg,
            "type": "background",
            "description": "店舗背景"
        })

    # トレーナー画像
    if trainer_name and trainer_images:
        for img in trainer_images:
            reference_images.append({
                "path": img,
                "type": "trainer",
                "description": f"トレーナー{trainer_name}"
            })

    with st.spinner("SNS投稿用プロンプトを生成中..."):
        try:
            print("📝 Claude APIを呼び出し中（SNSモード）...")
            optimized_prompt = convert_sns_prompt_with_claude(sns_params)
            print(f"✅ プロンプト生成完了: {optimized_prompt[:100]}...")

            with st.expander("最適化されたプロンプト（確認用）"):
                st.code(optimized_prompt, language="text")

        except Exception as e:
            print(f"❌ Claude APIエラー: {str(e)}")
            st.error(f"プロンプト変換エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return

    with st.spinner("画像を生成中... (30秒〜1分程度かかります)"):
        try:
            print("🎨 Gemini APIを呼び出し中...")
            result = generate_image_with_gemini(
                prompt=optimized_prompt,
                reference_images=reference_images,
                aspect_ratio=aspect_ratio,
                resolution="high"
            )

            if result["success"]:
                st.success("SNS投稿画像の生成が完了しました")

                st.image(result["image_path"], caption="生成されたSNS投稿画像", use_container_width=True)

                # ファイル名に投稿タイプを含める
                platform = sns_params.get("platform", "sns").replace(" ", "_").lower()
                with open(result["image_path"], "rb") as f:
                    st.download_button(
                        label="画像をダウンロード",
                        data=f,
                        file_name=f"firefitness_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png"
                    )

                # 投稿用テキストのヒント
                st.markdown("---")
                st.markdown("#### 投稿のヒント")
                if sns_params.get("platform") == "Instagram":
                    st.info("""
**共通ハッシュタグ（コピペ用）:**

#岡山パーソナルジム #岡山ダイエット #FIREFITNESS #3軸診断 #パーソナルトレーニング #岡山市 #ダイエット #姿勢改善 #岡山ジム
                    """)

                if result.get("text_response"):
                    with st.expander("Geminiからのコメント"):
                        st.write(result["text_response"])
            else:
                st.error(f"画像生成エラー: {result.get('error', '不明なエラー')}")

        except Exception as e:
            st.error(f"画像生成エラー: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


# =====================================
# メイン
# =====================================

def main():
    # ヘッダー
    fire_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>'''
    st.markdown(f'''
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
        <div style="
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #ff6b35 0%, #e55a2b 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);
        ">
            {fire_svg}
        </div>
        <div>
            <p class="main-header" style="margin: 0;">FIREFITNESS</p>
            <p style="color: rgba(255,255,255,0.5); font-size: 0.75rem; margin: 0; letter-spacing: 0.15em; text-transform: uppercase;">Image Generator</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Marketing Asset Creation Tool</p>', unsafe_allow_html=True)

    # API キーチェック
    gemini_key = os.getenv("GEMINI_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")

    if not gemini_key or not claude_key:
        st.error("APIキーが設定されていません。`.env`ファイルを確認してください。")
        st.code("""
# .envファイルに以下を設定：
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
        """)
        return

    # モード選択タブ
    tab1, tab2 = st.tabs(["宣材写真", "SNS投稿"])

    with tab1:
        render_promo_photo_mode()

    with tab2:
        render_sns_post_mode()

    # フッター
    st.markdown('''
    <div class="footer-text">
        <p style="margin: 0;">FIREFITNESS Image Generator v2.0</p>
        <p style="margin: 0.25rem 0 0 0; font-size: 0.7rem;">Powered by Claude API & Gemini API</p>
    </div>
    ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
