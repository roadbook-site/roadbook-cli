---
name: roadbook-onboarding
version: "0.2.0"
description: An interactive guide for onboarding users to the Roadbook system. Trigger this skill when a user asks about how to start using Roadbook, needs to understand the overall architecture, wants to initialize the environment, or needs help configuring their browser.
---

# Roadbook Onboarding Guide

Welcome to Roadbook! This skill is designed to guide new users through their first steps with the Roadbook system, from understanding its core philosophy to configuring their environment and running their first tasks.

## 1. The Pain Point: Why Roadbook?

When an AI Agent attempts to navigate traditional, human-centric websites, the experience is often like "blind men feeling an elephant." The web is complex, dynamic, and ever-changing. The cost of exploration is incredibly high, and rigid, standard automation scripts frequently break when the terrain (the UI) shifts.

Roadbook was created to solve this. Instead of rigid turn-by-turn navigation, Roadbook acts as a flexible, adaptive **Wilderness Trekking Guide**.

## 2. Core Concepts: The Wilderness Metaphor

To understand how Roadbook works, you need to understand its core metaphor. Roadbook treats web automation as an expedition into the wild.

- **Roadbook (The Expedition Log):** A Roadbook is not a rigid map; it's a log left by predecessors. It records key landmarks, offers environmental diagnostics, and provides actionable advice. When an Agent gets lost, the Roadbook explains what is missing and how to proceed step-by-step.
- **Agent (The Explorer):** The system's primary decision-maker. The Agent reads the Roadbook, and if a script fails, it uses visual and semantic understanding to explore new paths autonomously. The Agent always retains the highest control.
- **Guide (The Sherpa):** The Roadbook runtime system (CLI + Runtime). It carries the heavy load: managing browser operations, data movement, and scripts, while proactively offering environmental checks and guidance to the Explorer.
- **CLI (The Gear):** Your interactive toolbox. Errors here are not just failures—they are semantic guides providing actionable advice.
- **Context (The Backpack):** Your persistent memory. It holds the current Session, collected Data, and the Trace of the steps you've just taken.

### The Dual-Channel Strategy
Roadbook balances efficiency and generalization using a "Script First, Semantic Fallback" approach:
1. **Fast Path (Script Channel):** Pre-compiled scripts run instantly for stable pages.
2. **Slow Path (Semantic Channel):** If a script fails (e.g., UI changes) or doesn't exist, the Agent automatically takes over, reads the Roadbook, uses visual reasoning to navigate, and successfully completes the task before compiling a new script.

## 3. Browser Configuration: The Crucial Bridge

The browser is the most important bridge between the human, the Agent, and the web. Roadbook uses a lightweight, SDK-driven architecture to interact with the browser directly via Playwright, supporting a **"CDP Browser Takeover mode"**. This allows Roadbook to share the same login state and browser session seamlessly with you.

To get started, we must initialize the dedicated browser environment:

1. **Install Dependencies:** Ensure the Roadbook CLI and its dependencies are properly installed.
2. **Initialize Dedicated Browser:** Run the following command to start the configuration wizard:
   ```bash
   roadbook browser init
   ```
   This wizard will help you configure the browser executable path, CDP port (default 9222), and a dedicated user data directory to prevent mixing Roadbook data with your personal browsing data. It also allows you to create a desktop shortcut for easy access.
3. **Manage Browser Lifecycle:** Use the following commands to manage the dedicated browser:
   - `roadbook browser open`: Launch the dedicated browser using your configured profile.
   - `roadbook browser close`: Close the dedicated browser gracefully.
   - `roadbook browser kill`: Force release the CDP port if it's hanging.
   - `roadbook browser diagnose`: Diagnose your browser configuration and CDP connectivity.
4. **Visual Mapping:** The SDK handles complex CSS selectors and provides simplified UI interaction mechanisms, making it effortless for the Agent to interact with the page.

*Action for Agent:* When a user reaches this step, help them verify if Roadbook is properly installed and explicitly instruct them to run `roadbook browser init` to set up their persistent session profile. If they run into issues, suggest using `roadbook browser diagnose`.

## 4. Typical Reference Cases

Here is how Roadbook handles different scenarios:

### Scenario A: Cold Start (No Roadbook exists)
- **Flow:** The Agent searches and finds nothing.
- **Action:** Switch to "Explore Mode" -> The Agent freely browses and operates -> The session is recorded and saved as a brand new Roadbook.

### Scenario B: First Run or Update (Roadbook exists, but no valid script)
- **Flow:** The Agent loads the Markdown Roadbook.
- **Action:** It uses visual and semantic positioning to execute actions step-by-step. Upon successful completion, it generates a cached script for future use.

### Scenario C: Fast Path (Roadbook and valid script exist)
- **Flow:** The cached script is available.
- **Action:** Run the script directly. This results in millisecond-level response times with zero token consumption.

---

**Next Steps for the User:**
Ask the user: *"Would you like to start by running a Cold Start recording to create your first Roadbook?"*
