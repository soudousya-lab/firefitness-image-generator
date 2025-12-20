"""
FIREFITNESS 画像生成ツール - 初期セットアップスクリプト
フォルダ構成を作成し、必要な準備を行います
"""

import os
from pathlib import Path


def setup_directories():
    """必要なディレクトリ構造を作成"""
    
    base_dir = Path(__file__).parent
    
    # ディレクトリ構造
    directories = [
        # アセットディレクトリ
        "assets/trainers/okada",
        "assets/trainers/yamamoto",
        "assets/trainers/itakura",
        "assets/trainers/kuzumoto",
        "assets/backgrounds/shimadahonmachi",
        "assets/backgrounds/ifukucho",
        # 出力ディレクトリ
        "outputs",
    ]
    
    print("📁 ディレクトリを作成中...")
    print()
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path}")
    
    print()
    print("=" * 60)
    print()
    
    # .envファイルの確認
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("⚠️  .env ファイルが見つかりません")
        print("   .env.example を .env にコピーして、APIキーを設定してください")
        print()
        print("   コマンド例:")
        print("   cp .env.example .env")
        print()
    elif env_file.exists():
        print("✅ .env ファイルが存在します")
        print()
    
    # 画像配置の案内
    print("=" * 60)
    print()
    print("📷 画像ファイルを以下のフォルダに配置してください：")
    print()
    print("【トレーナー画像】")
    print("  assets/trainers/okada/      ← 岡田さんの写真（1〜2枚）")
    print("  assets/trainers/yamamoto/   ← 山本さんの写真（1〜2枚）")
    print("  assets/trainers/itakura/    ← 板倉さんの写真（1〜2枚）")
    print("  assets/trainers/kuzumoto/   ← 葛本さんの写真（1〜2枚）")
    print()
    print("【背景画像】")
    print("  assets/backgrounds/shimadahonmachi/  ← 島田本町店の内観")
    print("  assets/backgrounds/ifukucho/         ← 伊福町店の内観")
    print()
    print("📝 対応形式: .jpg, .jpeg, .png, .webp")
    print()
    print("=" * 60)
    print()
    print("🚀 セットアップ完了後、以下のコマンドでアプリを起動:")
    print()
    print("   streamlit run app.py")
    print()


def check_requirements():
    """必要なパッケージがインストールされているか確認"""
    
    required_packages = [
        "streamlit",
        "anthropic",
        "google.generativeai",
        "dotenv",
        "PIL"
    ]
    
    print("📦 パッケージ確認中...")
    print()
    
    missing = []
    
    for package in required_packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            elif package == "PIL":
                __import__("PIL")
            elif package == "google.generativeai":
                __import__("google.generativeai")
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    print()
    
    if missing:
        print("⚠️  以下のパッケージをインストールしてください:")
        print()
        print("   pip install -r requirements.txt")
        print()
    else:
        print("✅ すべてのパッケージがインストールされています")
        print()


if __name__ == "__main__":
    print()
    print("🔥 FIREFITNESS 画像生成ツール - セットアップ")
    print("=" * 60)
    print()
    
    setup_directories()
    
    print()
    check_requirements()
