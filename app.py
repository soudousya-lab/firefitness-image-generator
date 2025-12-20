"""
FIREFITNESS 画像生成アプリ
Streamlit + Claude API + Gemini API
"""

import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from prompt_converter import convert_prompt_with_claude
from image_generator import generate_image_with_gemini
import base64
from datetime import datetime

# 環境変数読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="FIREFITNESS 画像生成ツール",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS（ブランドカラー適用）
st.markdown("""
<style>
    .stApp {
        background-color: #f5f5f5;
    }
    .main-header {
        color: #0d2b45;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #ff6b35;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background-color: #e55a2b;
    }
    .info-box {
        background-color: #0d2b45;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #28a745;
        color: white;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 定数定義
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

SITUATIONS = {
    "カウンセリング・相談": "consultation",
    "姿勢チェック・診断": "posture_check",
    "セッション風景（落ち着いた雰囲気）": "training_session",
    "食事相談・説明": "nutrition_counseling",
    "施設内観（人物なし）": "interior",
    "図解・インフォグラフィック": "infographic",
    "目標達成で喜ぶ風景": "goal_achievement"
}

ASPECT_RATIOS = {
    "1:1（正方形）": "1:1",
    "4:5（縦長）": "4:5",
    "16:9（横長）": "16:9",
    "9:16（縦長・ストーリー）": "9:16",
    "4:3": "4:3",
    "3:2": "3:2",
    "21:9（ワイド）": "21:9"
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

# アセットパス
ASSETS_DIR = Path(__file__).parent / "assets"
TRAINERS_DIR = ASSETS_DIR / "trainers"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
OUTPUTS_DIR = Path(__file__).parent / "outputs"

# 出力ディレクトリ作成
OUTPUTS_DIR.mkdir(exist_ok=True)


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


def main():
    # ヘッダー
    st.markdown('<p class="main-header">🔥 FIREFITNESS 画像生成ツール</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">簡単な日本語入力から、ブランドに合った画像を生成します</p>', unsafe_allow_html=True)
    
    # API キーチェック
    gemini_key = os.getenv("GEMINI_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not gemini_key or not claude_key:
        st.error("⚠️ APIキーが設定されていません。`.env`ファイルを確認してください。")
        st.code("""
# .envファイルに以下を設定：
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
        """)
        return
    
    # サイドバー：設定
    with st.sidebar:
        st.header("📋 基本設定")
        
        # 店舗選択
        st.subheader("🏢 店舗（背景）")
        selected_location = st.selectbox(
            "店舗を選択",
            options=list(LOCATIONS.keys()),
            help="選択した店舗の背景画像が使用されます"
        )
        
        # 背景画像選択
        bg_dir = BACKGROUNDS_DIR / LOCATIONS[selected_location]
        bg_images = get_available_images(bg_dir)
        
        if bg_images:
            selected_bg = st.selectbox(
                "背景画像を選択",
                options=bg_images,
                format_func=lambda x: x.name
            )
            st.image(str(selected_bg), caption="選択中の背景", use_container_width=True)
        else:
            st.warning(f"背景画像がありません: {bg_dir}")
            selected_bg = None
        
        st.divider()
        
        # トレーナー選択
        st.subheader("👤 トレーナー")
        use_trainer = st.checkbox("トレーナーを登場させる", value=True)
        
        selected_trainer = None
        trainer_images = []
        
        if use_trainer:
            selected_trainer_name = st.selectbox(
                "トレーナーを選択",
                options=list(TRAINERS.keys())
            )
            
            trainer_dir = TRAINERS_DIR / TRAINERS[selected_trainer_name]
            trainer_images = get_available_images(trainer_dir)
            
            if trainer_images:
                selected_trainer = st.multiselect(
                    "参照画像を選択（複数可）",
                    options=trainer_images,
                    format_func=lambda x: x.name,
                    default=[trainer_images[0]] if trainer_images else []
                )
                
                # 選択した画像のプレビュー
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
        st.header("🎨 画像設定")
        
        # シチュエーション
        selected_situation = st.selectbox(
            "シチュエーション",
            options=list(SITUATIONS.keys()),
            help="生成する画像のシーン"
        )
        
        # クライアント（登場人物）
        selected_client = st.selectbox(
            "クライアント（登場人物）",
            options=list(CLIENT_TYPES.keys()),
            help="トレーナーと一緒に登場する人物"
        )
        
        # アスペクト比
        selected_ratio = st.selectbox(
            "アスペクト比",
            options=list(ASPECT_RATIOS.keys())
        )
        
        st.divider()
        
        # 追加指示
        st.subheader("✏️ 追加の指示（自由入力）")
        additional_prompt = st.text_area(
            "生成したい画像の詳細を日本語で入力",
            placeholder="例：笑顔で会話している様子、窓から自然光が入っている、清潔感のある雰囲気",
            height=100
        )
        
        # 詳細オプション
        with st.expander("🔧 詳細オプション"):
            include_text = st.checkbox("画像内にテキストを含める", value=False)
            if include_text:
                image_text = st.text_input(
                    "画像内に入れるテキスト",
                    placeholder="例：3軸診断、無料カウンセリング"
                )
            else:
                image_text = None
            
            mood = st.select_slider(
                "雰囲気",
                options=["落ち着いた", "やや落ち着いた", "ニュートラル", "やや活気ある", "活気ある"],
                value="やや落ち着いた"
            )
    
    with col2:
        st.header("📝 生成プロンプトプレビュー")
        
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
            "🎨 画像を生成する",
            use_container_width=True,
            type="primary"
        )
    
    # 生成処理
    if generate_button:
        print("=" * 50)
        print("🔥 生成ボタンが押されました")
        print("=" * 50)
        st.info("処理を開始します...")

        # 入力データ収集
        generation_input = {
            "location": selected_location,
            "situation": selected_situation,
            "trainer": selected_trainer_name if use_trainer else None,
            "client": selected_client if CLIENT_TYPES[selected_client] else None,
            "aspect_ratio": ASPECT_RATIOS[selected_ratio],
            "resolution": "high",
            "additional_prompt": additional_prompt,
            "image_text": image_text if include_text else None,
            "mood": mood
        }
        
        # 参照画像収集
        reference_images = []
        
        # 背景画像
        if selected_bg:
            reference_images.append({
                "path": selected_bg,
                "type": "background",
                "description": f"{selected_location}の店舗背景"
            })
        
        # トレーナー画像
        if use_trainer and selected_trainer:
            for img in selected_trainer:
                reference_images.append({
                    "path": img,
                    "type": "trainer",
                    "description": f"トレーナー{selected_trainer_name}"
                })
        
        with st.spinner("🔄 プロンプトを最適化中..."):
            try:
                print("📝 Claude APIを呼び出し中...")
                # Claude APIでプロンプト変換
                optimized_prompt = convert_prompt_with_claude(generation_input)
                print(f"✅ プロンプト生成完了: {optimized_prompt[:100]}...")

                with st.expander("📋 最適化されたプロンプト（確認用）"):
                    st.code(optimized_prompt, language="text")

            except Exception as e:
                print(f"❌ Claude APIエラー: {str(e)}")
                st.error(f"プロンプト変換エラー: {str(e)}")
                import traceback
                traceback.print_exc()
                return
        
        with st.spinner("🎨 画像を生成中... (30秒〜1分程度かかります)"):
            try:
                print("🎨 Gemini APIを呼び出し中...")
                # Gemini APIで画像生成
                result = generate_image_with_gemini(
                    prompt=optimized_prompt,
                    reference_images=reference_images,
                    aspect_ratio=ASPECT_RATIOS[selected_ratio],
                    resolution="high"
                )
                
                if result["success"]:
                    st.success("✅ 画像生成が完了しました！")
                    
                    # 生成画像表示
                    st.image(result["image_path"], caption="生成された画像", use_container_width=True)
                    
                    # ダウンロードボタン
                    with open(result["image_path"], "rb") as f:
                        st.download_button(
                            label="📥 画像をダウンロード",
                            data=f,
                            file_name=f"firefitness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                            mime="image/png"
                        )
                    
                    # 生成情報
                    if result.get("text_response"):
                        with st.expander("💬 Geminiからのコメント"):
                            st.write(result["text_response"])
                else:
                    st.error(f"画像生成エラー: {result.get('error', '不明なエラー')}")
                    
            except Exception as e:
                st.error(f"画像生成エラー: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # フッター
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>FIREFITNESS 画像生成ツール v1.0</p>
        <p>Powered by Claude API & Gemini API</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
