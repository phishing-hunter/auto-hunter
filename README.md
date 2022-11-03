# Hunting Automation

本リポジトリをクローンしてセットアップを完了させれば、
フィッシングサイトのハンティングを自動化することができます。

## 動作に必要な情報
以下のサービスに登録しAPIキーを取得してください。

* [phishing-hunter](https://phishing-hunter.com)
	* API Key
* [ngrok](https://ngrok.com/)
	* API Key
	* Auth Key
* [urlscan.io](https://urlscan.io/)
	* API Key
* [slack](https://slack.com/intl/ja-jp/help/articles/115005265063-Slack-%E3%81%A7%E3%81%AE-Incoming-Webhook-%E3%81%AE%E5%88%A9%E7%94%A8)
	* Incoming Webhook

## 環境変数の設定
```bash
$ echo "NGROK_AUTH=ngrokのauth key" > .env
$ echo "NGROK_API=ngrokのAPI key NGROK_AUTHではありません" >> .env
$ echo "API_BASE_URL=https://h99x7kgf7k.execute-api.ap-northeast-1.amazonaws.com/prod" >> .env
$ echo "PH_API_KEY=phishing hunter のAPIキー" >> .env
$ echo "URLSCAN_API=urlscan.ioのAPIキー" >> .env
$ echo "SLACK_WEBHOOK_URL=urlscan.ioのAPIキー" >> .env
```

## 監視キーワードの設定
```
$ cp config.yml.template config.yml
$ vim config.yml
```

## dockerの起動
```
$ docker-compose build
$ docker-compose up -d
```
