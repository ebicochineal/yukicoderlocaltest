# pyuki.py
yukicoderからテストケースダウンロード、自動でプログラムのテスト、テストケースの閲覧を行うスクリプトです  
日本語入力問題非対応  
リアクティブ問題非対応  
テストケースがダウンロードできなかった場合は入力サンプルでテストします  
pyuki.pyはPython3.5で実行できます  
テストケースダウンロードにyukicoderのREVEL_SESSIONの値も必要なのでブックマークレットを使って取得してください  
yukicoderからダウンロードするには ノーマル か ゆるふわ に設定する必要があります  
pyuki.pyにオプションでテストするプログラムファイルを指定することもできます  
テストするプログラムファイル名に問題ナンバーが入っていると問題ナンバーの入力を省略できます  
○ 0001.py, 1.py, 1.exe problem0001.exe, yukicoder0001.exe  
× 0001problem.exe, 0001test.exe

# bookmarklet.txt
ブラウザで空のブックマークを作りbookmarklet.txtの中身を空のブックマークのＵＲＬに入力  
yukicoderのサイト上で実行するとREVEL_SESSIONが表示されます

# setting.ini
言語別にコマンドの設定  
実行時に追加するパス  
作業ディレクトリなどの設定  
