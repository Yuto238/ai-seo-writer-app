import base64
import os
import re
from datetime import datetime
from typing import List, Optional

import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI


# =========================
# 初期設定
# =========================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


st.set_page_config(
    page_title="AI SEO Article Workbench",
    page_icon="✍️",
    layout="wide",
)


# =========================
# 共通関数
# =========================

def call_openai(system_prompt: str, user_prompt: str) -> str:
    """
    OpenAI APIを呼び出してテキストを生成する。
    APIキーがない場合はデモ用メッセージを返す。
    """

    if not client:
        return """
### デモモードです

OpenAI APIキーが設定されていないため、AI生成は実行されていません。

`.env` ファイルに以下を設定してください。

```env
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```
"""

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )
        return response.output_text

    except Exception as e:
        return f"""
### エラーが発生しました

```text
{e}
```

APIキー、モデル名、通信環境を確認してください。
"""


def count_characters(text: str) -> int:
    return len(text.replace("\n", ""))


def markdown_to_text(markdown_text: str) -> str:
    """
    Markdown形式をプレーンテキストに変換する。
    ヘッダー記号や装飾記号を削除し、可読性を保つ。
    """
    text = markdown_text

    # ヘッダー記号を削除
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)

    # コードブロックのマーカーを削除
    text = re.sub(r"```.*?\n", "", text, flags=re.MULTILINE)

    # インラインコード（バッククォート）を削除
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # 太字を削除
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)

    # イタリックを削除
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # リンクを削除
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # 余分な空白行をまとめる
    text = re.sub(r"\n\n\n+", "\n\n", text)

    return text.strip()


# =========================
# プロンプト
# =========================

ARTICLE_SYSTEM_PROMPT = """
あなたはVOD紹介SEO記事制作に強い編集者兼AIライターです。
以下の方針を必ず守ってください。

- 生成AIの出力をそのまま公開せず、人間確認が必要な箇所を明示する
- 配信状況、料金、キャンペーン、日付など変動情報は断定しない
- SEO記事として、検索意図、読者像、構成、タイトル、導入文、FAQ、メタディスクリプションを整理する
- 「作品名 配信 どこで見れる」「無料で見れる」「TVerで見れない」などの検索意図を重視する
- 記事の最終目的は比較を通じておすすめVODサービスへ自然に送客すること
- 出力はMarkdown形式
- 実務でそのまま使いやすいよう、見出しを明確にする
- 文章は日本語
"""

# =========================
# UI
# =========================

st.title("AI SEO Article Workbench")
st.caption("アニメ・ドラマ・映画の配信サービス紹介記事を作るためのAIライター支援ツール")

with st.sidebar:
    st.header("設定")

    article_type = st.selectbox(
        "記事ジャンル",
        [
            "アニメ配信記事",
            "ドラマ配信記事",
            "映画配信記事",
            "VOD比較記事",
        ],
    )

    tone = st.selectbox(
        "文体",
        [
            "わかりやすく丁寧",
            "親しみやすい",
            "企業メディア風",
            "SEO重視",
            "少しカジュアル",
        ],
    )

    st.divider()

    st.subheader("API状態")
    if OPENAI_API_KEY:
        st.success("OpenAI APIキー設定済み")
        st.caption(f"使用モデル：{OPENAI_MODEL}")
    else:
        st.warning("APIキー未設定")
        st.caption(".env に OPENAI_API_KEY を設定してください。")




# =========================
# 画像生成関数
# =========================

def build_image_prompt(
    theme: str,
    genre: str,
    usage: str,
    mood: str,
    include_elements: str,
    exclude_elements: str,
) -> str:
    """
    入力内容をもとに英語の画像生成プロンプトを作成する。
    """

    mood_map = {
        "明るい": "bright and cheerful",
        "やさしい": "soft and gentle",
        "かわいい": "cute and friendly",
        "高級感": "elegant and sophisticated",
        "アニメ風": "anime-style illustration",
        "シネマティック": "cinematic and dramatic",
        "落ち着いた": "calm and serene",
        "ポップ": "colorful and pop-art style",
    }

    genre_map = {
        "アニメ配信記事": "anime streaming service article",
        "ドラマ配信記事": "drama streaming service article",
        "映画配信記事": "movie streaming service article",
        "VOD比較記事": "video on demand comparison article",
    }

    usage_map = {
        "Web記事のアイキャッチ": "wide horizontal web article hero image with room for text overlay",
        "SNS投稿用": "social media post image, square or portrait format, eye-catching",
        "YouTubeサムネイル": "YouTube thumbnail, wide horizontal, bold visual",
        "ブログヘッダー": "blog header image, wide banner with clean minimal design",
    }

    mood_en = mood_map.get(mood, mood)
    genre_en = genre_map.get(genre, genre)
    usage_en = usage_map.get(usage, "wide horizontal web article hero image")

    include_en = include_elements.strip() if include_elements.strip() else "natural lighting, clean composition"
    exclude_en = exclude_elements.strip() if exclude_elements.strip() else "text, logo, real persons"

    prompt = (
        f"A {mood_en} illustration suitable for a {genre_en} article. "
        f"Style: {usage_en}. "
        f"Theme: {theme}. "
        f"Key visual elements: {include_en}. "
        f"Wide horizontal composition, clean layout, soft depth of field, "
        f"ample empty space on one side for article title text overlay. "
        f"Original character design, not based on any existing anime, manga, film, or real person. "
        f"No text, no logo, no watermark, no signature. "
        f"Avoid including: {exclude_en}. "
        f"High quality, web-ready, commercially usable image."
    )

    return prompt


def generate_image(prompt: str, size: str) -> Optional[bytes]:
    """
    OpenAI Image APIで画像を生成し、PNGバイトデータを返す。
    """

    if not client:
        return None

    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        n=1,
    )

    image_b64 = response.data[0].b64_json
    return base64.b64decode(image_b64)


def clean_page_text(html_text: str) -> str:
    """
    HTMLから本文テキストを抽出し、余分な空白を整理する。
    """

    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def extract_official_summary_text(source_text: str) -> str:
    """
    公式HP本文から「あらすじ」系セクションをできるだけ原文のまま抽出する。
    """

    if not source_text.strip():
        return ""

    keywords = [
        "あらすじ",
        "イントロダクション",
        "Introduction",
        "INTRODUCTION",
        "STORY",
        "Story",
        "ストーリー",
        "作品概要",
        "Synopsis",
        "Outline",
        "About",
    ]

    heading_patterns = [re.compile(rf"^\s*{re.escape(keyword)}\s*[:：\-]?\s*(.*)$", re.IGNORECASE) for keyword in keywords]

    def looks_like_next_heading(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False

        if any(pattern.match(stripped) for pattern in heading_patterns):
            return True

        short_line = len(stripped) <= 24 and not re.search(r"[。．.!?！？]$", stripped)
        all_caps = stripped.isupper() and len(stripped) <= 40
        return short_line or all_caps

    lines = source_text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        for pattern in heading_patterns:
            match = pattern.match(stripped)
            if not match:
                continue

            collected: List[str] = []
            inline_text = match.group(1).strip()
            if inline_text:
                collected.append(inline_text)

            for next_line in lines[index + 1 :]:
                next_stripped = next_line.rstrip()
                if not next_stripped.strip():
                    if collected:
                        collected.append("")
                    continue

                if collected and looks_like_next_heading(next_stripped):
                    break

                collected.append(next_stripped)

            extracted = "\n".join(collected).strip()
            if extracted:
                return extracted

    return ""


def fetch_page_text(url: str, max_chars: int = 12000) -> tuple[str, str]:
    """
    公式HPのHTMLを取得して本文テキスト化する。
    戻り値は (本文テキスト, エラーメッセージ)。
    """

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return "", f"URL本文の取得に失敗しました: {e}"

    try:
        page_text = clean_page_text(response.text)
    except Exception as e:
        return "", f"本文の解析に失敗しました: {e}"

    if not page_text:
        return "", "本文が取得できませんでした。"

    return page_text[:max_chars], ""


def discover_related_pages(base_url: str) -> list[str]:
    """
    入力された公式HP内から、STORY、STAFF、CAST、BOOKS、ON AIRなどの関連ページURLを探す。
    同一ドメイン内のURLのみ対象にする。
    
    Args:
        base_url: 検索対象のベースURL
        
    Returns:
        発見された関連ページのURLリスト（優先度順）
    """
    from urllib.parse import urlparse, urljoin, urlunparse
    
    try:
        # URLをパース
        parsed_base = urlparse(base_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        
        # ベースURLのHTMLを取得
        response = requests.get(
            base_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
            timeout=10,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 関連ページのキーワード（優先度順）
        priority_filenames = [
            "story.html", "storyline.html",
            "staffcast.html", "staff-cast.html",
            "character.html", "characters.html",
            "cast.html", "staff.html",
            "original.html", "original-work.html",
            "introduction.html", "about.html",
            "books.html", "book.html",
            "onair.html", "on-air.html", "broadcast.html",
            "music.html", "songs.html",
            "news.html", "news-info.html",
        ]
        
        priority_link_texts = [
            "STORY", "ストーリー",
            "INTRODUCTION", "イントロダクション", "作品概要",
            "ORIGINAL", "原作",
            "STAFF", "スタッフ",
            "CAST", "キャスト", "出演者",
            "CHARACTER", "キャラクター", "キャラ",
            "BOOKS", "本", "原作本",
            "ON AIR", "ONAIR", "放送", "配信",
            "MUSIC", "音楽", "主題歌",
            "NEWS", "ニュース", "最新情報",
        ]
        
        # ページ内のすべてのリンクを取得
        discovered_urls = {}  # {url: priority_score}
        
        for link in soup.find_all("a", href=True):
            href = link.get("href", "").strip()
            if not href:
                continue
            
            # 相対URLを絶対URLに変換
            try:
                absolute_url = urljoin(base_url, href)
            except Exception:
                continue
            
            # URLをパース
            parsed_url = urlparse(absolute_url)
            url_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # 同一ドメインのみ対象
            if url_domain != base_domain:
                continue
            
            # クエリ文字列やフラグメントを除去
            clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", ""))
            
            # 重複を避ける
            if clean_url in discovered_urls:
                continue
            
            # ベースURLと同じなら不要
            if clean_url == urlunparse((parsed_base.scheme, parsed_base.netloc, parsed_base.path, "", "", "")):
                continue
            
            priority_score = 0
            
            # ファイル名パターンでスコア計算
            path_lower = parsed_url.path.lower()
            for i, filename in enumerate(priority_filenames):
                if filename in path_lower:
                    priority_score += 1000 - i
                    break
            
            # リンクテキストでスコア計算
            link_text = link.get_text(strip=True).upper()
            for i, keyword in enumerate(priority_link_texts):
                if keyword.upper() in link_text:
                    priority_score += 500 - i
                    break
            
            # スコアが高い場合のみ追加
            if priority_score > 0:
                discovered_urls[clean_url] = priority_score
        
        # スコアが高い順にソート
        sorted_urls = sorted(discovered_urls.items(), key=lambda x: x[1], reverse=True)
        result_urls = [url for url, _ in sorted_urls[:10]]  # 最大10ページまで
        
        return result_urls
        
    except Exception as e:
        return []


def fetch_multi_page_text(base_url: str, discovered_urls: list[str], max_pages: int = 8) -> tuple[dict[str, str], List[str]]:
    """
    複数のページからテキストを取得し、URL別にまとめて返す。
    
    Args:
        base_url: ベースURL
        discovered_urls: discover_related_pages()で得たURL一覧
        max_pages: 最大ページ数
        
    Returns:
        (URLごとのテキスト辞書, エラーが発生したURLリスト)
    """
    
    urls_to_fetch = [base_url] + discovered_urls[:max_pages - 1]
    page_texts = {}
    failed_urls = []
    
    for url in urls_to_fetch:
        try:
            page_text, error = fetch_page_text(url, max_chars=8000)
            if error:
                failed_urls.append(url)
            else:
                page_texts[url] = page_text
        except Exception:
            failed_urls.append(url)
    
    return page_texts, failed_urls


def build_official_summary_prompt(page_text: str, url: str, genre: str) -> str:
    """
    公式HP本文の整理用プロンプトを作成する。
    複数ページのテキストに対応。
    """

    return f"""
以下の公式HP本文に含まれる情報だけをもとに出力してください。本文にない情報は推測せず、必ず「未確認」と書いてください。

公式あらすじはAIで言い換えたり要約したりせず、コード側で抽出した原文をそのまま使います。あなたは「小あらすじ」と作品情報の整理だけを行ってください。

【作品ジャンル】
{genre}

【情報元URL】
{url}

【公式HP本文（複数ページ統合）】
{page_text}

【出力要件】
- 小あらすじは100文字程度
- 公式あらすじの言い換えは禁止
- 本文にない情報は推測しない
- 不明な項目は「未確認」と記載する
- 出演者情報は本文で確認できる範囲のみを使う
- 複数ページから得た情報を統合して整理する
- 日付、配信情報、公開情報など変動しやすい情報は断定せず、必要に応じて「要確認」とする
- アニメの場合は、必ず Markdown表形式で「## キャラクター・声優」を出力する
- 表の列は「キャラクター | 声優」とする
- ドラマ/映画の場合は、Markdown表形式で「## キャラクター・俳優名」または「## 役名・俳優名」を出力する
- 表の列は「キャラクター（役名） | 声優（俳優名）」とする
- HTMLタグは使わない
- 最大15件まで

【出力形式】
【小あらすじ】
（100文字程度）

【原作情報】
（未確認なら未確認）

【作者情報】
（未確認なら未確認）

【放送・配信情報】
（未確認なら未確認）

【作品情報】
| 項目 | 内容 |
|---|---|
| 作品タイトル | |
| 放送開始日／公開日 | |
| 原作 | |
| 漫画 | |
| 監督 | |
| 総監督 | |
| シリーズ構成 | |
| 脚本 | |
| 制作会社 | |
| 主題歌 | |
| オープニングテーマ | |
| エンディングテーマ | |
| キャラクター：声優 | |
| 出演俳優 | |
| 外部リンク | {url} |

【キャラクター・声優または役名・俳優名】
アニメの場合は必ず以下の形式で出力する。

## キャラクター・声優

| キャラクター | 声優 |
|---|---|
| 例 | 例 |

ドラマ/映画の場合は以下の形式で出力する。

## 役名・俳優名

| 役名 | 俳優名 |
|---|---|
| 例 | 例 |

【記事用紹介文】
（SEO記事向けの短い紹介文）

【未確認項目】
・（本文で確認できなかった項目を列挙）

【公開前ファクトチェック】
・人間確認が必要な項目を3〜8件、簡潔に列挙
・例: 配信開始日、先行配信の有無、公式表記ゆれ、キャスト最新情報

【情報元URL】
{url}
"""


def generate_official_summary(page_text: str, url: str, genre: str) -> str:
    """
    取得済み本文をOpenAIで小あらすじと作品情報に整理する。
    """

    prompt = build_official_summary_prompt(page_text=page_text, url=url, genre=genre)
    system_prompt = """
あなたは編集部のリサーチ担当です。
公式HP本文に明記された情報のみを使って整理してください。
公式あらすじはコード側の抽出結果をそのまま使うため、AIでは変更しないでください。
公開前に人間確認が必要な項目は明示してください。
"""
    result = call_openai(system_prompt, prompt)
    result = re.sub(r"<br\s*/?>", "\n", result, flags=re.IGNORECASE)
    return result


def create_official_summary_download_text(result: str, url: str, genre: str) -> str:
    """
    ダウンロード用テキストを返す。
    """

    return f"""【作品ジャンル】
{genre}

{result}

【情報元URL】
{url}
"""


def build_vod_article_prompt(
    work_title: str,
    genre: str,
    official_summary: str,
    services_text: str,
    recommended_service: str,
    tone: str,
) -> str:
    """
    公式HP要約結果と配信サービス情報をもとに、VOD記事本文生成用プロンプトを作成する。
    """

    return f"""
あなたはVOD紹介記事の編集者です。
以下の入力情報だけを使って、Markdown形式で記事パーツを作成してください。

【重要ルール】
- 入力にない配信状況、料金、無料期間、キャンペーンは作らない
- 推測は禁止。不明は「未確認」または「要確認」
- サービス名は入力情報に含まれるものだけを記載
- ランキング表現（例: No.1）は入力にある場合のみ使用
- 公式あらすじを長く転載しない
- HTMLタグを使わない
- <br> を使わない
- 表はMarkdown表形式で出力する
- 変動情報（配信開始日、料金、無料期間、キャンペーン）は公開前に必ず人間確認が必要であることを明示する

【作品タイトル】
{work_title}

【作品ジャンル】
{genre}

【記事のトーン】
{tone}

【公式HP要約結果】
{official_summary}

【配信サービス情報（人間確認済み入力）】
{services_text}

【推したいサービス】
{recommended_service}

【出力形式】
## 記事冒頭文
- 視聴できる動画配信サービスを紹介する文
- 小あらすじ
- 原作情報
- 放送・配信情報
- 推したいサービスへの自然な導線

## 配信サービス比較表
必ず以下のヘッダで作成すること。

| 動画配信サービス | 配信状況 | 無料期間 | 月額料金 | 特徴 |
|---|---|---|---|---|
| サービス名 | 入力情報ベース | 要確認または入力情報 | 要確認または入力情報 | 入力情報ベース |

## おすすめ配信サービス紹介
- 推したいサービスを300文字程度で紹介
- 入力されていない数値情報（料金、無料期間、作品数、ランキング等）は書かない

## 作品情報一覧
以下の項目で表を作成し、確認できない項目は「未確認」。

| 項目 | 内容 |
|---|---|
| 作品タイトル | |
| 放送開始日／公開日 | |
| 原作 | |
| 作者 | |
| 漫画 | |
| 掲載媒体 | |
| 出版社 | |
| 監督 | |
| 総監督 | |
| シリーズ構成 | |
| 脚本 | |
| 制作会社 | |
| 主題歌 | |
| OPテーマ | |
| EDテーマ | |
| 放送局 | |
| 先行配信 | |
| 一般配信 | |
| 外部リンク | |

## キャラクター・声優 / 出演者
- アニメの場合:

| キャラクター | 声優 |
|---|---|
| 名前 | 名前 |

- ドラマ・映画の場合:

| 役名 | 俳優名 |
|---|---|
| 名前 | 名前 |

## FAQ
次の5問を含めること。
- 『{work_title}』はどこで見られますか？
- 『{work_title}』は無料で見られますか？
- 『{work_title}』の放送開始日はいつですか？
- 『{work_title}』の原作はありますか？
- 『{work_title}』のキャスト・声優は誰ですか？

回答では、入力情報にない内容は断定せず「最新情報は各公式サイトをご確認ください」と明記すること。

## 公開前ファクトチェック
- 人間確認が必要な項目を5〜8件で列挙すること。
- 最低限、作品名表記、配信開始日、配信形態（見放題/レンタル）、料金、無料期間、キャンペーン有無、公式URLを含めること。

## 注意書き
※配信状況・料金・無料期間・キャンペーン内容は変更される場合があります。最新情報は各動画配信サービスの公式サイトをご確認ください。
"""


tab_official, tab_vod, tab_image, tab_article = st.tabs(
    [
        "公式HP要約",
        "VOD記事本文生成",
        "アイキャッチ画像生成",
        "記事構成生成",
    ]
)


# =========================
# タブ2：VOD記事本文生成
# =========================

with tab_vod:
    st.header("VOD記事本文生成")

    st.info(
        "公式HP要約結果と人間確認済みの配信サービス情報をもとに、配信比較・FAQ・CTAまで含めたVOD紹介記事パーツをMarkdownで生成します。"
    )

    if "vod_official_summary_input" not in st.session_state:
        st.session_state["vod_official_summary_input"] = st.session_state.get("official_hp_summary_result", "")

    col_vod1, col_vod2 = st.columns(2)

    with col_vod1:
        vod_work_title = st.text_input(
            "作品タイトル",
            value="",
            placeholder="例：愛してるゲームを終わらせたい",
            key="vod_work_title",
        )

        vod_genre = st.selectbox(
            "作品ジャンル",
            ["アニメ", "ドラマ", "映画", "その他"],
            key="vod_genre",
        )

        if st.button("公式HP要約結果を読み込む", key="vod_load_official_summary"):
            st.session_state["vod_official_summary_input"] = st.session_state.get("official_hp_summary_result", "")

        vod_official_summary = st.text_area(
            "公式HP要約結果",
            height=240,
            placeholder="公式HP要約タブで生成した結果を貼り付けてください。",
            key="vod_official_summary_input",
        )

    with col_vod2:
        vod_services_text = st.text_area(
            "配信サービス情報",
            height=220,
            placeholder=(
                "例:\n"
                "DMM TV：4月19日（日）より見放題配信開始。\n"
                "ABEMA：4月14日（火）より先行配信。\n"
                "dアニメストア：4月14日（火）より先行配信。\n"
                "U-NEXT：配信状況は要確認。"
            ),
            key="vod_services_text",
        )

        vod_recommended_service = st.text_input(
            "推したいサービス",
            value="",
            placeholder="例：DMM TV",
            key="vod_recommended_service",
        )

        vod_tone = st.selectbox(
            "記事のトーン",
            ["わかりやすく丁寧", "親しみやすい", "SEO記事風", "比較記事風"],
            key="vod_tone",
        )

    if st.button("VOD記事本文を生成する", type="primary", key="vod_generate_btn"):
        if not vod_work_title.strip():
            st.error("作品タイトルを入力してください。")
        elif not vod_official_summary.strip():
            st.error("公式HP要約結果を入力してください。")
        elif not vod_services_text.strip():
            st.error("配信サービス情報を入力してください。")
        else:
            prompt = build_vod_article_prompt(
                work_title=vod_work_title.strip(),
                genre=vod_genre,
                official_summary=vod_official_summary.strip(),
                services_text=vod_services_text.strip(),
                recommended_service=vod_recommended_service.strip() or "未指定",
                tone=vod_tone,
            )

            system_prompt = """
あなたはVOD記事編集の実務担当者です。
入力テキストに含まれる情報のみを使って、事実ベースで整理してください。
配信状況・料金・無料期間・キャンペーンを推測で補完してはいけません。
不明な情報は「未確認」または「要確認」としてください。
人間確認が必要な情報は「公開前に要確認」と明記してください。
出力はMarkdown形式で、HTMLタグや <br> は使用しないでください。
"""

            with st.spinner("VOD記事本文パーツを生成中です..."):
                vod_result = call_openai(system_prompt, prompt)

            vod_result = re.sub(r"<br\s*/?>", "\n", vod_result, flags=re.IGNORECASE)
            st.session_state["vod_article_result"] = vod_result

    if st.session_state.get("vod_article_result"):
        st.subheader("生成結果")
        st.markdown(st.session_state["vod_article_result"])

        vod_text = markdown_to_text(st.session_state["vod_article_result"])
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📄 Markdownとしてダウンロード",
                data=st.session_state["vod_article_result"],
                file_name="vod_article_body.md",
                mime="text/markdown",
                key="vod_article_md_download",
            )
        with col_dl2:
            st.download_button(
                label="📋 テキストとしてダウンロード",
                data=vod_text,
                file_name="vod_article_body.txt",
                mime="text/plain",
                key="vod_article_text_download",
            )


# =========================
# タブ4：記事構成生成
# =========================

with tab_article:
    st.header("記事構成生成")

    st.info(
        "「作品名 配信 どこで見れる」「無料で見れる」「TVerで見れない」などのSEOキーワードを狙う、VOD送客記事の構成を作成します。"
    )

    col1, col2 = st.columns(2)

    with col1:
        work_title = st.text_input(
            "作品名・商品名・テーマ",
            value="地獄楽",
            placeholder="例：地獄楽、あんぱん、君の名は。など",
        )

        keyword = st.text_input(
            "狙いたいSEOキーワード",
            value="地獄楽 配信 どこで見れる 無料",
            placeholder="例：作品名 配信 どこで見れる / TVerで見れない / 無料で見れる",
        )

        reader_problem = st.text_area(
            "読者の悩み",
            value="地獄楽をどの配信サービスで見られるのか、無料で見られる方法やTVer対応の有無を知りたい。",
            height=100,
        )

    with col2:
        article_goal = st.text_area(
            "記事の目的",
            value="読者に視聴方法をわかりやすく伝え、比較を通じておすすめVODサービスの利用につなげる。",
            height=100,
        )

        must_include = st.text_area(
            "必ず入れたい内容",
            value="配信サービス比較、TVer対応有無、無料視聴の注意点、作品情報、FAQ、CTA",
            height=100,
        )

    if st.button("記事構成を生成する", type="primary"):
        user_prompt = f"""
以下の条件で、VOD紹介SEO記事制作のための設計書を作成してください。

【記事ジャンル】
{article_type}

【作品名・商品名・テーマ】
{work_title}

【狙いたいSEOキーワード】
{keyword}

【読者の悩み】
{reader_problem}

【記事の目的】
{article_goal}

【必ず入れたい内容】
{must_include}

【文体】
{tone}

【出力してほしい内容】
1. 検索意図
2. 想定読者
3. SEOタイトル案を5つ
4. メタディスクリプションを3つ
5. H2・H3構成
6. 導入文
7. 本文の書き出し例
8. FAQを5つ
9. CTA導線案
10. 競合記事との差別化ポイント
11. 人間が確認すべきファクトチェック項目
12. CMS入稿用Markdownテンプレート
"""

        result = call_openai(ARTICLE_SYSTEM_PROMPT, user_prompt)
        st.markdown(result)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="📄 Markdownとしてダウンロード",
                data=result,
                file_name="article_plan.md",
                mime="text/markdown",
            )

        with col2:
            text_result = markdown_to_text(result)
            st.download_button(
                label="📋 テキストとしてダウンロード",
                data=text_result,
                file_name="article_plan.txt",
                mime="text/plain",
            )


# =========================
# タブ3：アイキャッチ画像生成
# =========================

with tab_image:
    st.header("アイキャッチ画像生成")

    st.write("記事テーマや雰囲気を入力すると、Web記事用のアイキャッチ画像を生成します。")

    col1, col2 = st.columns(2)

    with col1:
        img_theme = st.text_input(
            "記事テーマ・作品名",
            value="",
            placeholder="例：保育園の先生、春アニメ特集、美容サロン紹介",
            key="img_theme",
        )

        img_genre = st.selectbox(
            "記事ジャンル",
            [
                "アニメ配信記事",
                "ドラマ配信記事",
                "映画配信記事",
                "VOD比較記事",
            ],
            key="img_genre",
        )

        img_usage = st.selectbox(
            "画像の用途",
            [
                "Web記事のアイキャッチ",
                "SNS投稿用",
                "YouTubeサムネイル",
                "ブログヘッダー",
            ],
            key="img_usage",
        )

        img_mood = st.selectbox(
            "画像の雰囲気",
            [
                "明るい",
                "やさしい",
                "かわいい",
                "高級感",
                "アニメ風",
                "シネマティック",
                "落ち着いた",
                "ポップ",
            ],
            key="img_mood",
        )

    with col2:
        img_size = st.selectbox(
            "画像サイズ",
            [
                "1536x1024",
                "1024x1024",
                "1024x1536",
            ],
            key="img_size",
        )

        img_include = st.text_area(
            "入れたい要素",
            value="",
            placeholder="例：明るい室内、やさしい表情の人物、窓から入る光、横長構図、余白あり",
            height=120,
            key="img_include",
        )

        img_exclude = st.text_area(
            "入れたくない要素",
            value="文字, ロゴ, 実在人物, 暗い雰囲気",
            height=120,
            key="img_exclude",
        )

    st.divider()

    # プロンプト生成ボタン
    if st.button("画像生成プロンプトを作成する", key="gen_prompt_btn"):
        if not img_theme.strip():
            st.error("記事テーマ・作品名を入力してください。")
        else:
            generated_prompt = build_image_prompt(
                theme=img_theme,
                genre=img_genre,
                usage=img_usage,
                mood=img_mood,
                include_elements=img_include,
                exclude_elements=img_exclude,
            )
            st.session_state["image_prompt"] = generated_prompt

    if "image_prompt" in st.session_state:
        st.subheader("生成された画像プロンプト")
        st.code(st.session_state["image_prompt"], language="text")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="📋 プロンプトをテキストでダウンロード",
                data=st.session_state["image_prompt"],
                file_name="image_prompt.txt",
                mime="text/plain",
                key="prompt_download",
            )

        st.divider()

        # 画像生成ボタン
        if st.button("画像を生成する", type="primary", key="gen_image_btn"):
            if not OPENAI_API_KEY:
                st.error(
                    "OpenAI APIキーが設定されていません。`.env` に `OPENAI_API_KEY` を設定してください。"
                )
            else:
                with st.spinner("画像を生成中です。30〜60秒ほどかかります..."):
                    try:
                        image_bytes = generate_image(
                            prompt=st.session_state["image_prompt"],
                            size=img_size,
                        )
                        st.session_state["generated_image"] = image_bytes
                    except Exception as e:
                        error_msg = str(e)
                        st.error(f"画像生成中にエラーが発生しました。\n\n```\n{error_msg}\n```")
                        st.warning(
                            "よくある原因:\n"
                            "- APIキーが正しく設定されていない\n"
                            "- `gpt-image-1` モデルへのアクセス権がない（Organization Verificationが必要な場合があります）\n"
                            "- ネットワークエラーまたはAPIの一時的な障害"
                        )

    if "generated_image" in st.session_state and st.session_state["generated_image"]:
        st.subheader("生成された画像")

        try:
            st.image(
                st.session_state["generated_image"],
                use_column_width=True,
            )

            st.download_button(
                label="🖼️ PNGとしてダウンロード",
                data=st.session_state["generated_image"],
                file_name="eyecatch_image.png",
                mime="image/png",
                key="image_download",
            )

        except Exception as e:
            st.error("画像の表示中にエラーが発生しました。")
            st.code(str(e))
            st.info("画像データが壊れているか、Streamlitの表示引数が環境に対応していない可能性があります。")

    st.caption(
        "⚠️ 生成画像の商用利用については、OpenAIの利用規約および画像生成モデルのポリシーを必ず確認してください。"
    )


# =========================
# タブ1：公式HP要約
# =========================

with tab_official:
    st.header("公式HP要約")

    st.info(
        "この機能は、公式HPのURLを貼り付けることで、公式サイト本文をもとに作品のあらすじや作品情報を整理する機能です。AIに事実を推測させるのではなく、取得した公式情報をもとに要約するため、記事制作時のファクトチェックや下書き作成に活用できます。"
    )

    official_hp_url = st.text_input(
        "公式HPのURL",
        value="",
        placeholder="https://example.com/anime-official",
        key="official_hp_url",
    )

    official_hp_genre = st.selectbox(
        "作品ジャンル",
        [
            "アニメ",
            "ドラマ",
            "映画",
            "その他",
        ],
        key="official_hp_genre",
    )

    official_hp_manual_text = st.text_area(
        "公式本文の手動貼り付け欄",
        value="",
        placeholder="公式HP本文をそのまま貼り付けてください。URL取得できない場合の補助として使えます。",
        height=220,
        key="official_hp_manual_text",
    )

    if st.button("公式HPを要約する", type="primary", key="official_hp_summary_btn"):
        if not official_hp_url.strip():
            st.error("公式HPのURLを入力してください。")
        else:
            # ステップ1: 関連ページを発見
            with st.spinner("関連ページを発見中です..."):
                discovered_urls = discover_related_pages(official_hp_url.strip())
            
            # ステップ2: 発見されたページを表示
            if discovered_urls:
                with st.expander(f"発見されたページ ({len(discovered_urls)} 件)"):
                    for url in discovered_urls:
                        st.write(f"- {url}")
            
            # ステップ3: 複数ページの本文を取得
            with st.spinner("複数ページの本文を取得中です..."):
                page_texts_dict, failed_urls = fetch_multi_page_text(
                    official_hp_url.strip(),
                    discovered_urls,
                    max_pages=8
                )
            
            if not page_texts_dict:
                st.error("ページの本文取得に失敗しました。URLを確認してください。")
            else:
                # ステップ4: 複数ページのテキストを統合
                combined_text_parts = []
                for url, page_text in page_texts_dict.items():
                    combined_text_parts.append(f"【ページ: {url}】\n{page_text}")
                
                combined_text = "\n\n---\n\n".join(combined_text_parts)
                
                # 手動貼り付け本文がある場合は追加
                if official_hp_manual_text.strip():
                    combined_text += "\n\n---\n\n【手動貼り付け本文】\n" + official_hp_manual_text.strip()
                
                source_text = combined_text

                if not source_text.strip():
                    st.error("取得本文が空のため、要約できません。")
                else:
                    st.session_state["official_hp_page_text"] = source_text[:2000]
                    st.session_state["official_hp_source_text"] = source_text
                    st.session_state["official_hp_url_value"] = official_hp_url.strip()
                    st.session_state["official_hp_genre_value"] = official_hp_genre
                    st.session_state["official_hp_discovered_urls"] = discovered_urls
                    st.session_state["official_hp_page_count"] = len(page_texts_dict)

                    # ステップ5: 公式あらすじを抽出
                    official_summary_raw = extract_official_summary_text(source_text)
                    if not official_summary_raw:
                        official_summary_raw = "公式あらすじは取得できませんでした"

                    if len(source_text) < 800:
                        st.warning("取得できた本文が少ないため、情報が不足している可能性があります")

                    # ステップ6: AIで整理
                    if OPENAI_API_KEY:
                        with st.spinner("本文から小あらすじと作品情報を整理中です..."):
                            ai_result = generate_official_summary(
                                page_text=source_text,
                                url=official_hp_url.strip(),
                                genre=official_hp_genre,
                            )
                    else:
                        ai_result = f"""【小あらすじ】
未確認（APIキー未設定のため自動要約は未実行）

【原作情報】
未確認

【作者情報】
未確認

【放送・配信情報】
未確認

【作品情報一覧】
| 項目 | 内容 |
|---|---|
| 作品タイトル | 未確認 |
| 放送開始日／公開日 | 未確認 |
| 原作 | 未確認 |
| 漫画 | 未確認 |
| 監督 | 未確認 |
| 総監督 | 未確認 |
| シリーズ構成 | 未確認 |
| 脚本 | 未確認 |
| 制作会社 | 未確認 |
| 主題歌 | 未確認 |
| オープニングテーマ | 未確認 |
| エンディングテーマ | 未確認 |
| キャラクター：声優 | 未確認 |
| 出演俳優 | 未確認 |
| 外部リンク | {official_hp_url.strip()} |

【キャラクター：声優、または役名：俳優名】
未確認

【記事用紹介文】
未確認

【未確認項目】
・APIキー未設定のため、本文の整理を実行していません
・{len(page_texts_dict)}ページから本文を取得しています

【情報元URL】
{official_hp_url.strip()}
"""

                    final_report = (
                        f"【公式あらすじ】\n{official_summary_raw}\n\n"
                        f"{ai_result.strip()}\n\n"
                        f"【情報元URL】\n{official_hp_url.strip()}\n"
                        f"【取得元ページ数】\n{len(page_texts_dict)} ページ"
                    )

                    if OPENAI_API_KEY:
                        st.info(
                            f"この機能では、{len(page_texts_dict)}ページから取得した公式情報をもとに、AIが情報を抽出・整理しています。"
                        )
                    else:
                        st.info(f"APIキー未設定のため、{len(page_texts_dict)}ページ分の本文取得結果のみを使ったデモモードです。")

                    st.session_state["official_hp_summary_result"] = final_report
                    st.session_state["official_hp_official_summary"] = official_summary_raw
                    st.session_state["official_hp_ai_result"] = ai_result
                
                if failed_urls:
                    st.warning(
                        f"以下の {len(failed_urls)} ページの取得に失敗しました:\n"
                        + "\n".join(f"- {url}" for url in failed_urls)
                    )


    if "official_hp_summary_result" in st.session_state and st.session_state["official_hp_summary_result"]:
        st.subheader("公式あらすじ")
        st.code(st.session_state.get("official_hp_official_summary", "公式あらすじは取得できませんでした"), language="text")

        st.subheader("要約結果")
        st.markdown(st.session_state["official_hp_ai_result"])

        st.download_button(
            label="テキストとしてダウンロード",
            data=create_official_summary_download_text(
                result=st.session_state["official_hp_summary_result"],
                url=st.session_state.get("official_hp_url_value", ""),
                genre=st.session_state.get("official_hp_genre_value", "未確認"),
            ),
            file_name="official_hp_summary.txt",
            mime="text/plain",
            key="official_hp_summary_download",
        )

    if "official_hp_page_text" in st.session_state and st.session_state["official_hp_page_text"]:
        with st.expander("取得した本文テキスト（先頭1200文字）"):
            st.write(st.session_state["official_hp_page_text"][:1200])

    st.divider()
    st.code(
        "この機能は、公式HPのURLを貼り付けることで、公式サイト本文をもとに作品のあらすじや作品情報を整理する機能です。AIに事実を推測させるのではなく、取得した公式情報をもとに要約するため、記事制作時のファクトチェックや下書き作成に活用できます。",
        language="text",
    )
