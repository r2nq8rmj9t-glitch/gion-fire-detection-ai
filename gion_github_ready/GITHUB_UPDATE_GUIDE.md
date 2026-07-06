# GitHub更新手順

## 初回だけ行う作業

```bash
cd "C:\Users\Oonak\OneDrive\Desktop\gion\gion_fire_ai\photoidentify"
git init
git add .
git commit -m "Initial commit: Gion fire detection AI"
git branch -M main
git remote add origin https://github.com/<GitHubユーザー名>/<リポジトリ名>.git
git push -u origin main
```

## 作品を修正した後の更新

```bash
git status
git add .
git commit -m "Update portfolio app"
git push
```

## よく使う確認コマンド

```bash
git status
git log --oneline --max-count=5
git remote -v
```

## 公開前チェック

- `.env` をGitHubに上げない
- `db.sqlite3` をGitHubに上げない
- `media/uploads/` をGitHubに上げない
- `media/results/` をGitHubに上げない
- `media/feedback/` をGitHubに上げない
- `__pycache__/` と `.mypy_cache/` をGitHubに上げない
- APIキー、パスワード、個人情報をコード内に書かない

## モデルファイルについて

このリポジトリでは、現在のモデルファイルは1ファイル100MB未満です。  
ただし、今後100MBを超えるモデルを扱う場合は、通常のGitではなくGit LFSや外部ストレージを検討してください。
