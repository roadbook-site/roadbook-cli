# Roadbook

**Roadbook** is a semantic-based, non-rigid web automation framework designed to be resilient against UI changes. 

Unlike traditional web automation tools that rely on fragile XPath or CSS selectors, Roadbook uses **semantic landmarks** and natural language cues to interact with web pages via the Chrome DevTools Protocol (CDP). This allows your automation scripts (called "roadbooks") to survive layout redesigns and DOM changes.

## ✨ Key Features

- **Semantic Landmarks**: Target elements intuitively by their roles, names, and visual context (e.g., "the login button" or "the search input") rather than their exact position in the DOM.
- **Resilient & Non-Rigid**: Capable of adapting to minor webpage updates without breaking your automation pipelines.
- **Human-in-the-Loop**: Gracefully handle edge cases, CAPTCHAs, or complex scenarios by pausing execution (`wait_for_human`), allowing human intervention, and resuming seamlessly.
- **CDP Native**: Fast, precise, and reliable browser control powered directly by the Chrome DevTools Protocol.

## 🚀 Installation

Install Roadbook via pip:

```bash
pip install roadbook
```

## 🏁 Quick Start

1. **Start Chrome with Remote Debugging Enabled**
   
   To allow Roadbook to control your browser, launch Chrome with the CDP port open (e.g., port 9224).
   ```bash
   # Windows
   chrome.exe --remote-debugging-port=9224
   
   # macOS
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9224
   ```

2. **Run a Roadbook**

   You can execute a Roadbook YAML file directly using the CLI. By default, it will connect to the open CDP port:

   ```bash
   roadbook run library/my_first_roadbook.yaml
   ```

## 🎯 Why Roadbook?

We built Roadbook to address common pitfalls in modern web automation:
1. **Semantic Effectiveness**: Elements can be reliably located using natural language landmarks instead of rigid code paths.
2. **High Fault Tolerance**: Automation can remain robust even when underlying HTML structures shift.
3. **Synergistic Collaboration**: Bots aren't perfect. Graceful failure and manual handoffs ("wait for human" capabilities) are critical for robust long-running automation tasks.
