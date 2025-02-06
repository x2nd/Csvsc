@echo off

REM カレントディレクトリをバッチファイルのあるディレクトリに設定
pushd %~dp0

REM PyInstallerを実行してexeファイルを作成
echo Building csvsc.exe...
.\.venv\Scripts\pyinstaller.exe --clean csvsc.spec

echo Building 数式確認ツール.exe...
.\.venv\Scripts\pyinstaller.exe --clean expression_evaluator_gui.spec

REM カレントディレクトリを元に戻す
popd

echo csvsc.exe has been created in the dist folder.
pause