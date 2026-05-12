# AI SEO Article Workbench

AIライターの実務を想定した、SEO記事制作支援Webアプリです。

## 主な機能

- 検索意図分析
- 想定読者の整理
- SEOタイトル案作成
- メタディスクリプション作成
- H2・H3構成作成
- 導入文作成
- FAQ作成
- リライト診断
- 読みやすさチェック
- ファクトチェックリスト
- CMS入稿用Markdownテンプレート作成

## フォルダ構成

```text
ai-seo-writer-app/
├── app.py
├── requirements.txt
├── .env.example
└── README.md
```

## 使い方

### 1. フォルダに移動

```bash
cd ai-seo-writer-app
```

### 2. 仮想環境を作成

Macの場合：

```bash
python -m venv venv
source venv/bin/activate
```

Windowsの場合：

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. ライブラリをインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数を設定

`.env.example` をコピーして `.env` という名前に変更します。

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### 5. 起動

```bash
streamlit run app.py
```

ブラウザでアプリが開きます。

## 面接での説明例

このアプリは、AIライターの実務を想定して作成したSEO記事制作支援ツールです。

単にAIに本文を書かせるのではなく、検索意図の整理、想定読者の設定、記事構成、タイトル案、FAQ、メタディスクリプション、リライト診断、ファクトチェックまでを一つの流れで行えるようにしました。

特に、配信状況・料金・キャンペーン・日付など、AIが誤りやすい情報については、人間が確認すべき項目として出力する設計にしています。

生成AIのスピードを活かしつつ、SEO記事としての品質と正確性を担保することを意識しました。
