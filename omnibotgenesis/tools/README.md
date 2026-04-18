# OMNIX Tools

Command-line utilities for development and operations. These are **NOT** part of the core application logic.

## Structure

```
tools/
├── telegram/           # Telegram bot utilities
│   ├── chat_with_bot.py
│   ├── get_my_telegram_id.py
│   └── send_telegram_message.py
└── operations/         # Operational tools
    ├── generate_investor_report.py
    └── migration_watchdog.py
```

## Telegram Tools

### Get Your Telegram User ID

```bash
python tools/telegram/get_my_telegram_id.py
```

Then send any message to the bot. It will reply with your User ID.

### Send a Message

```bash
python tools/telegram/send_telegram_message.py <USER_ID> "Your message"
```

### Interactive Chat

```bash
python tools/telegram/chat_with_bot.py <USER_ID>
```

## Operations Tools

### Generate Investor Report

```bash
python tools/operations/generate_investor_report.py
```

Generates a PDF report from PostgreSQL trade data.

### Migration Watchdog

```bash
python tools/operations/migration_watchdog.py
```

Monitors database for orphan positions after profile migrations.

## Note

For code verification and version consistency checks, use pytest:

```bash
pytest tests/test_code_verification.py -v
pytest tests/test_version_consistency.py -v
```
