# ⚡ Stack Overflow Search Pro (FASM x64 Edition)

Высокопроизводительный, легковесный нативный клиент для поиска по **Stack Overflow** и **ru.stackoverflow**, написанный на чистом ассемблере **x86-64** для **Flat Assembler (FASM)** с поддержкой **прямого живого поиска через официальный StackExchange API v2.3**.

---

## 🌟 Ключевые возможности

- **Реальный живой поиск через интернет (Live API Search)**:
  - Прямое HTTPS-соединение через `WININET.DLL` к `https://api.stackexchange.com/2.3/search/advanced`.
  - Автоматическое переключение эндпоинтов:
    - Вкладка **English (SO)** ➔ `site=stackoverflow`
    - Вкладка **Russian (RU)** ➔ `site=ru.stackoverflow`
  - Быстрый встроенный JSON-парсер на ассемблере:
    - Извлечение `title`, `score`, `answer_count`, `view_count`, `is_answered`, `display_name`, `link`, `question_id`, `quota_remaining`.
    - Декодирование HTML-сущностей (`&#39;`, `&quot;`, `&amp;`, `&lt;`, `&gt;`).
    - Автоматическая трансляция UTF-8 в кодовую страницу Windows (CP1251) через Win32 API (`MultiByteToWideChar` + `WideCharToMultiByte`).
  - Учёт квоты запросов: отображение оставшегося лимита в статусной строке (`API Quota: 275/300`).
  - Офлайн-режим: при отсутствии сети автоматически загружается встроенная база проверенных решений.

- **Современный Fluent Dark UI в стиле `copyprintwindows` и `screenvideo`**:
  - Все кнопки с флагом `BS_OWNERDRAW` и ручной отрисовкой через `WM_DRAWITEM` и `RoundRect`.
  - Оранжевый бейдж `[ SO ]` с логотипом и яркий заголовок `Search Pro`.
  - Быстрые однокликовые теги: `python`, `javascript`, `asyncio`, `fastapi`, `rust`, `c++`, `docker`.
  - Сегментированные вкладки (**Pill Tabs**) с подсветкой активного раздела Stack Overflow Orange (`#F48024`).
  - Высококонтрастный блок деталей: тёмный фон `#111622` с кристально-белым шрифтом **Consolas** (`#FCF8F8`).

- **Действия в один клик (1-Click Productivity)**:
  - `[ Copy Question ]` — копирование полного описания и метаданных в буфер обмена Windows.
  - `[ Copy Solution ]` — копирование ссылки / кода решения в буфер обмена.
  - `[ Save Bookmark ]` — сохранение выбранного вопроса в локальный файл `bookmarks.txt`.
  - `[ Browser ]` — открытие оригинальной страницы в браузере по умолчанию.

---

## 📁 Структура проекта

```
C:\proekts\StackOverflowAPI\asm\
├── stackoverflow.asm      # Главный исходный код FASM x64 (Live HTTPS API + Owner-Drawn UI)
├── manifest.xml           # Манифест Common-Controls 6.0 + PerMonitorV2 High DPI
├── build.bat              # Скрипт сборки через C:\asm\hdd\FASM.EXE
├── run.bat                # Скрипт быстрого запуска приложения
├── StackOverflowSearch.exe# Скомпилированный PE64 бинарник (28 KB)
└── README.md              # Документация проекта
```

---

## 🛠️ Сборка и запуск

### Быстрая сборка через Batch:
```cmd
cd C:\proekts\StackOverflowAPI\asm
build.bat
```

### Прямая компиляция через FASM:
```cmd
C:\asm\hdd\FASM.EXE stackoverflow.asm StackOverflowSearch.exe
```

### Запуск:
```cmd
run.bat
```
или дважды кликните по `StackOverflowSearch.exe`.
