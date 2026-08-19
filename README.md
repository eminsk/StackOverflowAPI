# Stack Overflow Search Pro 🚀 (v2.0)

A modern, high-performance, and lightweight desktop application for searching **Stack Overflow (English)** and **Russian Stack Overflow** simultaneously. Built with Python and **CustomTkinter**, with an elegant dark/light UI, rich syntax highlighting, and 1-click code block copying.

![Icon](icon.png)

## ✨ Features

- **⚡ Lightweight & Fast**: Built with CustomTkinter instead of heavy UI frameworks—minimal memory footprint and instant startup.
- **🌐 Bilingual Search**: Simultaneous or dedicated search across **Stack Overflow (English)** and **Stack Overflow (Russian)**.
- **🎨 Modern Professional UI**:
  - Polished Dark / Light / System themes with Stack Overflow brand accents.
  - Split master-detail view with clean question cards, answer counters, score pills, view counts, and tag chips.
  - Green glowing banners for accepted solutions.
- **💡 Rich Content & Code Highlighting**:
  - Full Question & Answer formatting (paragraphs, blockquotes, lists, headings).
  - Code blocks with Pygments syntax highlighting (Python, JavaScript, C++, Rust, Go, SQL, Bash, HTML, CSS, etc.).
  - **1-Click Smart Copy**: Instant clipboard copy with visual feedback animation.
- **💬 Full Comments Support**: Collapsible/expandable comment threads for both questions and individual answers.
- **🚀 Advanced Sorting**: Sort results by *Relevance*, *Votes*, *Newest (Creation)*, or *Recent Activity*.
- **🧵 Non-Blocking Concurrency**: Thread-safe asynchronous background fetching keeps the UI silky smooth at all times.
- **📦 Standalone Executable**: Can be compiled into a single compact `.exe` file without heavy Qt dependencies.

---

## 🛠 Installation & Running

### Developer (from source with `uv`)
```bash
# Clone repository
git clone https://github.com/eminsk/StackOverflowAPI.git
cd StackOverflowAPI

# Install dependencies (using uv)
uv sync

# Run the app
uv run main.py
```

### Running Tests
```bash
uv run python tests/test_components.py
```

---

## 🏗 Standalone Compilation (Nuitka)

To compile the application into a single standalone Windows `.exe` file:

```bash
uv run build_exe.py
```

This generates an ultra-compact `StackOverflowGUI.exe` in the root folder without any heavy Qt runtime dependencies.

---

## 📋 Requirements

- Windows 10 / 11
- Python 3.12+
- Active Internet connection (for Stack Exchange API)

---

## 📄 License

MIT License
