# Scheduling the Job Scraper

This guide explains how to set up automated daily execution of the job scraper on macOS.

## Option 1: LaunchD (Recommended for macOS)

LaunchD is the native macOS scheduling system and is more reliable than cron.

### Setup Steps

1. **Review the configuration file**
   
   Open `com.user.job_scraper.plist` and verify the paths are correct:
   - Script path: `/Users/carrienon/Desktop/code-project/job_scraper/run_task.sh`
   - Working directory: `/Users/carrienon/Desktop/code-project/job_scraper`
   - Time: 9:00 AM daily (modify Hour/Minute if needed)

2. **Copy the plist file to LaunchAgents**
   
   ```bash
   cp com.user.job_scraper.plist ~/Library/LaunchAgents/
   ```

3. **Load the launch agent**
   
   ```bash
   launchctl load ~/Library/LaunchAgents/com.user.job_scraper.plist
   ```

4. **Verify it's loaded**
   
   ```bash
   launchctl list | grep job_scraper
   ```

### Management Commands

```bash
# Start the job immediately (for testing)
launchctl start com.user.job_scraper

# Stop the scheduled job
launchctl stop com.user.job_scraper

# Unload (disable) the job
launchctl unload ~/Library/LaunchAgents/com.user.job_scraper.plist

# Reload after making changes
launchctl unload ~/Library/LaunchAgents/com.user.job_scraper.plist
launchctl load ~/Library/LaunchAgents/com.user.job_scraper.plist
```

### Check Logs

```bash
# View standard output
tail -f /Users/carrienon/Desktop/code-project/job_scraper/stdout.log

# View errors
tail -f /Users/carrienon/Desktop/code-project/job_scraper/stderr.log

# View task log
tail -f /Users/carrienon/Desktop/code-project/job_scraper/task.log
```

### Customize Schedule

Edit the plist file's `StartCalendarInterval` section:

```xml
<!-- Run every day at 9:00 AM -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

For multiple times per day, use an array:

```xml
<!-- Run at 9 AM and 6 PM -->
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

---

## Option 2: Cron (Alternative)

Cron is the traditional Unix scheduler and works on macOS.

### Setup Steps

1. **Give cron Full Disk Access** (macOS Catalina+)
   - Go to System Preferences → Security & Privacy → Privacy
   - Select "Full Disk Access"
   - Click the lock to make changes
   - Add `/usr/sbin/cron`

2. **Edit crontab**
   
   ```bash
   crontab -e
   ```

3. **Add the schedule** (runs daily at 9 AM)
   
   ```cron
   # Job Scraper - runs every day at 9:00 AM
   0 9 * * * /Users/carrienon/Desktop/code-project/job_scraper/run_task.sh >> /Users/carrienon/Desktop/code-project/job_scraper/cron.log 2>&1
   ```

4. **Save and exit** (press `ESC`, then type `:wq` in vim)

### Cron Syntax Reference

```
*    *    *    *    *
│    │    │    │    │
│    │    │    │    └─── Day of week (0-7, Sunday = 0 or 7)
│    │    │    └──────── Month (1-12)
│    │    └───────────── Day of month (1-31)
│    └────────────────── Hour (0-23)
└─────────────────────── Minute (0-59)
```

### Examples

```cron
# Every day at 9 AM
0 9 * * * /path/to/run_task.sh

# Every day at 9 AM and 6 PM
0 9,18 * * * /path/to/run_task.sh

# Every weekday (Mon-Fri) at 9 AM
0 9 * * 1-5 /path/to/run_task.sh

# Every 6 hours
0 */6 * * * /path/to/run_task.sh

# Twice daily: 8 AM and 8 PM
0 8,20 * * * /path/to/run_task.sh
```

### Management Commands

```bash
# List current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Remove all cron jobs
crontab -r

# View cron logs (if logging to file)
tail -f /Users/carrienon/Desktop/code-project/job_scraper/cron.log
```

---

## Testing the Setup

Before relying on the scheduled task, test it manually:

```bash
# Make the script executable
chmod +x /Users/carrienon/Desktop/code-project/job_scraper/run_task.sh

# Run manually to test
/Users/carrienon/Desktop/code-project/job_scraper/run_task.sh

# Check the logs
tail -f /Users/carrienon/Desktop/code-project/job_scraper/task.log
```

---

## Troubleshooting

### Script doesn't run

1. **Check permissions**
   ```bash
   chmod +x /Users/carrienon/Desktop/code-project/job_scraper/run_task.sh
   ```

2. **Verify Python path**
   ```bash
   which python3
   # Update PYTHON variable in run_task.sh if needed
   ```

3. **Check environment variables**
   Make sure `.env` file exists and has correct values

4. **Review logs**
   ```bash
   cat /Users/carrienon/Desktop/code-project/job_scraper/stderr.log
   cat /Users/carrienon/Desktop/code-project/job_scraper/task.log
   ```

### LaunchD not working

```bash
# Check if loaded
launchctl list | grep job_scraper

# View detailed status
launchctl print gui/$(id -u)/com.user.job_scraper

# Check system logs
log show --predicate 'process == "launchd"' --last 1h | grep job_scraper
```

### Cron not working

1. Verify cron has Full Disk Access in System Preferences
2. Check cron is running: `ps aux | grep cron`
3. Test the script manually first
4. Use absolute paths in crontab

---

## Notifications (Optional)

### macOS Notification

Install `terminal-notifier`:

```bash
brew install terminal-notifier
```

Add to the end of `run_task.sh`:

```bash
terminal-notifier -title "Job Scraper" -message "Daily job scraping completed" -sound default
```

### Email Notification

Configure mail and add to `run_task.sh`:

```bash
echo "Job scraper completed at $(date)" | mail -s "Job Scraper Report" your_email@example.com
```

---

## Recommended Setup

For best results on macOS:

1. ✅ Use **LaunchD** (more reliable than cron)
2. ✅ Set time to when your computer is awake (e.g., 9 AM)
3. ✅ Test manually first
4. ✅ Monitor logs for the first few days
5. ✅ Keep your Mac on or scheduled to wake at the task time

---

## System Preferences for Scheduled Tasks

To ensure scheduled tasks run reliably:

1. **Prevent Sleep During Task**
   - System Preferences → Battery → Power Adapter
   - Set "Turn display off after" to a reasonable time
   - Uncheck "Put hard disks to sleep when possible"

2. **Schedule Computer to Wake** (optional)
   ```bash
   sudo pmset repeat wakeorpoweron MTWRFSU 08:55:00
   ```
   This wakes the computer at 8:55 AM daily (5 minutes before the 9 AM task)
