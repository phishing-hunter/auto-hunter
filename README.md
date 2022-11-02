# Hunting Automation

本リポジトリをクローンしてセットアップを完了させれば、
フィッシングサイトのハンティングを自動化することができます。

## 動作に必要な情報
以下のサービスに登録しAPIキーを取得してください。

* https://phishing-hunter.com
	* API Key
* https://ngrok.com/
	* API Key
	* Auth Key
* https://urlscan.io/
	* API Key

## 環境変数の設定
```bash
$ echo "NGROK_AUTH=ngrokのauth key" > .env
$ echo "NGROK_API=ngrokのAPI key NGROK_AUTHではありません" >> .env
$ echo "API_BASE_URL=https://h99x7kgf7k.execute-api.ap-northeast-1.amazonaws.com/prod" >> .env
$ echo "PH_API_KEY=phishing hunter のAPIキー" >> .env
$ echo "URLSCAN_API=urlscan.ioのAPIキー" >> .env
```

## dockerの起動
```
$ docker-compose build
$ docker-compose up -d
```
