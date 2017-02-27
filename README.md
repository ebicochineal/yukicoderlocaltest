# pyuki.py
yukicoderからテストケースダウンロード、プログラムのテスト、テストケースの閲覧を行うスクリプト  
日本語入力問題非対応  
リアクティブ問題非対応  
テストケースがダウンロードできなかった場合は入力サンプルでテスト  
pyuki.pyはPython3.5で実行  
テストケースダウンロードにyukicoderのREVEL_SESSIONの値が必要。ブラウザでクッキーを表示し取得  
yukicoderからダウンロードするには ノーマル か ゆるふわ に設定  
テストするプログラムファイル名に問題ナンバーが入っていると問題ナンバーの入力を省略できる  
○ 0001.py, 1.py, 1.exe problem0001.exe, yukicoder0001.exe  
× 0001problem.exe, 0001test.exe

# setting.ini
実行時に追加するパス  
言語別コマンドの設定  