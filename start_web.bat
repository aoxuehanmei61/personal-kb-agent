@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动知识库 Agent 网页版...

start "" cmd /c "python app.py"

timeout /t 4 /nobreak >nul
start "" http://127.0.0.1:8000

echo 已启动，浏览器地址：http://127.0.0.1:8000
echo 关闭本窗口不会停止服务，要停止请关掉弹出的那个终端窗口。
pause
