# AiNiee CLI (Optimized Edition)

<div align="center">
  <img src="https://img.shields.io/badge/Interface-CLI%20%2F%20TUI-0078D4?style=for-the-badge&logo=windows-terminal&logoColor=white" alt="CLI">
  <img src="https://img.shields.io/badge/Runtime-uv-purple?style=for-the-badge&logo=python&logoColor=white" alt="uv">
  <img src="https://img.shields.io/badge/Status-Optimized-success?style=for-the-badge" alt="Status">
</div>

<br/>

[English](README_EN.md) | [简体中文](README.md)

**AiNiee CLI** is an engineering-focused refactor of the [AiNiee](https://github.com/NEKOparapa/AiNiee) core logic, designed for command-line environments.

This project introduces **`uv`**, a modern Python package manager, and implements significant stability optimizations for the underlying runtime. By taking control of IO streams and exception handling, we have built a robust TUI environment perfect for long-running tasks, headless server deployments, and automated workflows.

> **🚧 Note**: To minimize environment configuration issues, this project is deeply integrated with `uv`. One-click launch scripts (`Launch.bat` and `Launch.sh`) will be available in future updates.

---

## ✨ Key Optimizations

### 🛡️ Runtime Stability
*   **IO Stream Cleaning & Hijacking**: Refactored the capture logic for Standard Output/Error (Stdout/Stderr). This effectively blocks redundant noise from underlying dependencies (like TensorFlow or C++ bindings), preventing TUI tearing or crashes and ensuring log readability in headless environments.

### ⚙️ Workflow & Configuration
*   **Intelligent Format Input/Conversion**: An optimized input processing pipeline. Supports a fully automated closed-loop operation ("Identify -> Convert -> Translate -> Restore") for non-standard formats (e.g., .mobi/.azw3), significantly simplifying pre-processing steps.
*   **Multi-Profile System (Profiles)**: Introduces a profile management system. You can create, clone, and switch between multiple configuration sets (e.g., separating settings for "Fast Translation" vs. "High-Quality Polishing"). All profiles are stored in isolation.\n*   **Live Mission Control**: **[New]** Introduces a new TUI task status and control center, supporting:
    *   **Dynamic Concurrency Adjustment**: Real-time increase or decrease of concurrent threads using `+` and `-` keys during task execution.
    *   **API Key Hot-Swap**: Force API key rotation using the `K` key to handle specific API call limits.
    *   **Web Monitoring Panel [New]**: Press the `M` key to instantly launch a background WebServer and open your browser to monitor the current task. The TUI panel will enter a "takeover mode," synchronizing all logs and status to the web interface in real-time.
    *   **System Status Monitoring**: A bottom status bar that displays real-time system operational status (Normal/Fixing/Warning/Error) and dynamically changes the panel border color.
    *   **Cost and Time Estimation**: Before task startup, automatically estimates total Token consumption, approximate cost for online APIs, and Estimated Time of Arrival (ETA), prominently displayed in the log pane (for reference only).
*   **Visual Interactive Experience**: A modern TUI built on `Rich`, featuring real-time performance monitoring (RPM/TPM), split-screen logging, and a BIOS-like interactive settings menu.
*   **[New] Plugin Architecture**:
    *   Introduces a brand-new plugin system, allowing for safe and modular feature extensions without altering the core codebase.
    *   **Built-in RAG Plugin**: Comes with an out-of-the-box RAG (Retrieval-Augmented Generation) Context Plugin. When enabled, it automatically retrieves historical translations to provide crucial context for long-form content, significantly improving terminological and stylistic consistency.
    *   **Centralized Management**: Both the main CLI menu and the Web UI feature a dedicated "Plugin Management" page, allowing you to discover and toggle all available plugins with a single click.
*   **[New] Intelligent Task Queue System**:
    *   **Multi-Modal Queue Management**: Create, edit, and delete translation task queues in both TUI interactive menus and WebServer visual interfaces.
    *   **Flexible Queue Scheduling**: Dynamic queue ordering support - WebServer interface offers mouse drag-and-drop sorting, while TUI interface provides keyboard-driven interactive reordering.
    *   **Hot Task Modification**: During queue execution, modify pending task parameters in real-time via WebServer without stopping the current running task. All queue changes are displayed with operation logs in the TUI console.
    *   **Batch Processing Optimization**: Pre-configure multiple tasks with different files or translation strategies, the system will execute them sequentially, perfect for large-scale translation workflows.
*   **[New] Thinking Mode Enhancement**:
    *   **Universal Platform Compatibility**: Fixed thinking mode compatibility issues across multiple AI platforms, now supporting all mainstream online API platforms and third-party gateways.
    *   **Smart Parameter Configuration**: Thinking mode settings are now permanently displayed in all interfaces regardless of platform constraints, with different compatibility warnings for online APIs vs local models.
    *   **Unified Interface Experience**: Fixed inconsistent display of thinking mode parameters between CLI menus and Web dashboard, ensuring a unified user experience.

---

## 🚀 Quick Start

This project provides multiple startup methods. Choose the one that best suits your use case.

## 🚀 Method 1: One-Click Launch (Recommended)

### 1. Get the Code
```bash
git clone https://github.com/ShadowLoveElysia/AiNiee-CLI.git
cd AiNiee-CLI
```

### 2. Environment Setup (First Run)

**Windows:**
```batch
Double-click prepare.bat
```

**Linux / macOS:**
```bash
chmod +x prepare.sh
./prepare.sh
```

The prepare script automatically:
- Detects and installs `uv` (if not installed)
- Creates virtual environment
- Installs all project dependencies

### 3. Launch Application

After environment setup, simply run:

**Windows:**
```batch
Double-click Launch.bat
```

**Linux / macOS:**
```bash
./Launch.sh
```

---

## 🛠️ Method 2: Manual Configuration (Advanced Users)

If you prefer to configure the environment manually:

### 1. Install uv

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux / macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Android (Termux) - Method 1 (Direct Installation):**
```bash
# Update package sources
pkg update && pkg upgrade
# Install Python if not already installed
pkg install python
# Install uv via pip
pip install uv
```

**Android (Termux) - Method 2 (Proot-Distro Ubuntu):**
```bash
# Install proot-distro
pkg install proot-distro
# Install Ubuntu environment
proot-distro install ubuntu
# Login to Ubuntu environment
proot-distro login ubuntu
# Install uv in Ubuntu
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> **📱 Termux Users**: For mobile devices, we recommend using the **WebServer mode with online API** for the best experience. The web interface is optimized for touch interactions and remote monitoring.

### 2. Get the Code
```bash
git clone https://github.com/ShadowLoveElysia/AiNiee-CLI.git
cd AiNiee-CLI
```

### 3. Instant Launch
No need to manually create virtual environments or install pip dependencies. Simply run `uv run` to handle the environment automatically:

```bash
# Automatically sync dependencies and start the CLI (Interactive Menu)
uv run ainiee_cli.py
```

---

## 💻 Command-Line Arguments (Non-Interactive Mode)
**[New]** This project supports launching translation or export tasks directly via command-line arguments, suitable for script integration and automation.

**Translation Task Example:**
```bash
uv run ainiee_cli.py translate "H:\\Novels\\MyBook.txt" -o "H:\\Novels\\MyBook_Output" -p MyProfile -s Japanese -t Chinese --resume --yes
```

**Queue Task Example:**
```bash
uv run ainiee_cli.py queue --queue-file "H:\\Novels\\my_queue.json" --yes
```

**Argument Description:**
*   `translate` / `polish` / `export` / `queue`: Specifies the task type.
*   `H:\\Novels\\MyBook.txt`: (Positional argument) Input file or folder path.
*   `-o, --output`: Specifies the output path.
*   `-p, --profile`: Specifies the configuration profile name.
*   `-s, --source`: Specifies the source language.
*   `-t, --target`: Specifies the target language.
*   `--type`: Specifies the project type (e.g., `Txt`, `Epub`, `MTool`).
*   `--resume`: Automatically resumes the task if a cache is detected.
*   `--yes`: Non-interactive mode; automatically answers `yes`.
*   **[New] Advanced Overrides:**
    *   `--threads`: Concurrent thread counts.
    *   `--rounds`: Max execution rounds.
    *   `--retry`: Max retry counts.
    *   `--timeout`: API timeout in seconds.
    *   `--platform`: Override target platform.
    *   `--model`: Override model name.
    *   `--api-url`: Override API URL.
    *   `--api-key`: Override API Key.
    *   `--lines` / `--tokens`: Override batch size.
    *   `--pre-lines`: Context lines to include.
    *   `--failover`: `on/off` toggle for API failover.
    *   `--think-depth`: Thinking mode depth level (0-10000, 0 to disable).
    *   `--thinking-budget`: Thinking mode token budget limit.
    *   `--queue-file`: Specifies the task queue JSON file path (only for `queue` task type).

---

## 📖 Menu Overview

Once launched, you can navigate the following features via the interactive menu:

*   **Start Translation / Polishing**: Core translation and polishing tasks (supports automatic resume).
*   **Export Only**: Quick export mode for existing cache files.
*   **Task Queue**: **[New]** Intelligent task queue management center for batch task configuration and execution.
*   **Profiles**: **[New]** Center for switching and managing configuration profiles.
*   **Settings / API Settings**: Categorized parameter settings with hot-reload support.
*   **Glossary**: Preview and apply prompt templates.
*   **Start Web Server**: **[New]** Launch the modern Web Dashboard.

---

## 🌐 Web Dashboard

**[New]** For a more intuitive experience, this project now includes a React-based Web Dashboard.

### How to Start
1.  Run `uv run ainiee_cli.py` to enter the main menu.
2.  Select **12. Start Web Server**.
3.  The program will automatically detect your LAN IP and start the service (default port `8000`), opening the dashboard in your default browser.

### Features
*   **Visual Dashboard**: Real-time charts showing RPM, TPM, and task progress.
*   **Network Access**: Monitor your translation tasks remotely via LAN IP. You can also use tunneling tools (e.g., `frp`, `cloudflared`) for external network access.
*   **Profile Management**: Create, rename, delete, or switch configuration profiles directly from the web UI.
*   **[New] Queue Management Center**: Intuitive queue management interface with mouse drag-and-drop task reordering, real-time task parameter editing, and queue item addition/deletion. All operations sync with TUI console logs.
*   **[New] Thinking Mode Configuration**: Complete thinking mode parameter configuration interface with compatibility hints and optimization suggestions for different AI platforms.
*   **[New] Plugin Center**: A dedicated plugin management page in the Web UI allows users to intuitively enable or disable advanced features like RAG through a card-based interface.
*   **State Recovery**: Automatically synchronizes task status, logs, and chart history even after a page refresh.

> **⚠️ Important Note**:
> **The Web Dashboard is currently in Beta and may have compatibility issues with certain devices (e.g., mobile browsers). If you require maximum stability (e.g., for very large batch tasks), please continue to use the native TUI mode.**

---

## 🛠️ Architecture

This project utilizes a **Wrapper / Adapter** pattern:

*   **Core**: The original AiNiee core business logic remains unchanged.
*   **Adapter Layer**: `ainiee_cli.py` acts as an anti-corruption layer, responsible for environment isolation, exception interception, and resource scheduling.
*   **Runtime**: Managed by `uv` to ensure consistency and startup speed.

---

## ⚠️ Disclaimer

*   This project is an unofficial optimized CLI branch of AiNiee, focusing on operational experience and engineering stability.
*   The core translation algorithms remain consistent with the original version. Please adhere to the original usage license.
*   This tool is intended for personal learning and legal use only.

---

<div align="center">
  Made with 💻 and ☕ by ShadowLoveElysia
  <br>
  Based on the original work by NEKOparapa
</div>