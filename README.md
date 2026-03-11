# DiffDog 🐕

**DiffDog** (invoked as `bark`) is a CLI tool that sniffs through your daily git commits across multiple repositories and uses LLM (Groq) to bark out a clean, formatted daily update summary. It automatically copies the result to your clipboard.

## 🛠 Installation

### Using uv (Recommended)
```bash
uv tool install diffdog
```

### Using pip
```bash
pip install diffdog
```

---

## ⚙️ Setup

You need a `config.yaml` file to get started.

1. **Get an API Key:** Create a free key at https://console.groq.com/keys
2. **Create your config:** Create a `config.yaml` with the following structure:

```yaml
author: "Your Name"
groq_key: "gsk_xxxx..."
model: "llama-3.3-70b-versatile" # Optional
no_copy: false                  # Optional
repos:
  - "~/projects/work-app"
  - "~/projects/side-hustle"
titles:
  - "Work App"
  - "Side Project"
```
*Note: The `author` field must have either the name or email you commit with, it's used to get `your` commits from your repos.*
*Note: The number of `repos` must match the number of `titles`.*

3. **Initialize the tool:**
```bash
bark -c path/to/your/config.yaml
```

---

## 🚀 Usage

**Generate and copy summary to clipboard:**
```bash
bark
```

**Print summary without copying to clipboard:**
```bash
bark --no-copy
```

**View current configuration:**
```bash
bark --show-conf
```

### 🔄 Updating Configuration
If you need to change your settings:
1. Run `bark --show-conf > config.yaml` to save your current settings to a file.
2. Edit the `config.yaml` file with your changes.
3. Re-assign it by running `bark -c config.yaml`.