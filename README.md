# Stack Overflow Search Pro 🚀 (v2.1)

A modern, high-performance, and lightweight desktop application for searching **Stack Overflow (English)** and **Russian Stack Overflow** simultaneously. Built with Python and **CustomTkinter**, featuring an elegant dark/light developer UI, rich inline syntax formatting, 1-click code block copying, offline bookmarks, and real-time result filtering.

![Icon](icon.png)

---

## ✨ Features

- **⚡ Lightweight & Fast**: Built with CustomTkinter instead of heavy Qt runtimes—instant startup, minimal RAM footprint, and smooth scrolling.
- **🌐 Bilingual Search**: Simultaneous or dedicated search across **Stack Overflow (English)** and **Stack Overflow (Russian)** with dynamic result counts.
- **🎨 Modern Professional UI & Design**:
  - Polished **Dark**, **Light**, and **System** palettes inspired by modern developer environments (Catppuccin Mocha & GitHub Light).
  - Clear visual hierarchy, subtle layered surfaces, and Stack Overflow brand orange accents.
  - Active question card highlight with glowing accent borders.
  - Prominent emerald banner for accepted solutions (`✓ ACCEPTED SOLUTION`).
- **💡 Rich Content & Inline Formatting**:
  - Rich HTML rendering with **inline code chips** (`` `code` ``), **bold**, *italics*, and **clickable hyperlinks** that open in your browser.
  - Headings, blockquotes, lists, and horizontal dividers.
  - Pygments syntax-highlighted code blocks (Python, JavaScript, TypeScript, C++, Rust, Go, SQL, Bash, HTML, CSS, Docker, etc.).
  - **↩ Code Wrap Toggle**: Easily switch code blocks between horizontal scroll and word wrap with 1 click.
  - **📋 1-Click Smart Copy**: Copy code blocks, full questions, answers, or links in clean Markdown format with instant visual checkmark feedback.
- **⭐ Offline Bookmarks / Favorites**:
  - Save any question and solution for quick offline reference with 1 click (`☆ Save` / `★ Saved`).
  - Dedicated **⭐ Bookmarks** tab with persistent JSON storage and instant retrieval.
- **⚡ Quick Search Topic Chips**:
  - One-click topic buttons (`python`, `javascript`, `react`, `fastapi`, `asyncio`, `pandas`, `docker`, `c++`, `rust`) for instant queries.
- **🔍 Real-Time Results Filter**:
  - Instant client-side filter bar above results to quickly filter loaded questions by title or tag.
- **⬇ Pagination ("Load More")**:
  - Infinite scroll loading: fetch additional pages (`+25 questions`) seamlessly without losing scroll position.
- **💬 Smooth In-Place Comments**:
  - Expand and collapse comment threads in-place without screen flicker or scroll position jumping.
- **📊 Live API Quota Monitoring**:
  - Status bar displays real-time Stack Exchange API quota remaining (`⚡ API Quota: 298 / 300`).
- **⌨ Global Keyboard Shortcuts**:
  - `Ctrl + K` or `Ctrl + F`: Instantly focus search bar and select query.
  - `Escape`: Clear search focus.
  - `Ctrl + B` or `Ctrl + D`: Toggle bookmark on currently viewed question.
  - `F5`: Reload current question and answers.
- **🧵 Crash-Proof Thread-Safe Queue**:
  - Asynchronous background threads dispatch updates via a thread-safe message queue, ensuring zero GUI freezes and maximum stability across all Python versions.

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
uv run python -m unittest discover -s tests
```

---

## 🏗 Standalone Compilation (Nuitka)

To compile the application into a single standalone Windows `.exe` file without heavy Qt dependencies:

```bash
uv run build_exe.py
```

This generates `StackOverflowGUI.exe` in the root folder.

---

## 📋 Requirements

- Windows 10 / 11
- Python 3.12+
- Active Internet connection (for Stack Exchange API)

---

## 📄 License

MIT License
