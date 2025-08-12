#!/bin/bash
# run_task.sh

# 设置时间日志
echo "=== Job started at $(date) ===" >> /Users/carrienon/Desktop/codeStudy/job_scraper/task.log

# 启动 Chrome 远程调试模式（后台运行）
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome_selenium" \
  &

# 等待 Chrome 启动
sleep 5

# 进入项目目录
cd /Users/carrienon/Desktop/codeStudy/job_scraper || exit

# 执行 scraper.py
/opt/homebrew/bin/python3 scraper.py

# 执行 sync_to_notion.py
/opt/homebrew/bin/python3 sync_to_notion.py

# 发送邮件（这里用 macOS 自带的 mail 命令）
# echo "任务完成于 $(date)" | mail -s "定时任务完成通知" your_email@example.com

echo "=== Job finished at $(date) ===" >> /Users/carrienon/Desktop/codeStudy/job_scraper/task.log
