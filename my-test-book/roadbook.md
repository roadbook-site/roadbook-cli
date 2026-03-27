---
id: "my-test-book"
name: "my_test_book"
version: "1.0"
owner: "user"
generator: "Agent/Roadbook"
platform: "desktop"
description: ""
entry_url: "https://www.example.com"
tags: []
inputs: 
  sample_param: "example_value"
outputs: {}
---

## initialization
**ID**: 696f9
**Type**: setup
**Description**: Verify browser environment (connection method), site constraints, and authentication state.
**URL**: `https://www.example.com`
**Locators**: `body`

**Constraints**:
- `force_headful`: false
- `stealth_mode`: false
- `viewport`: 1280x720
- `global_delay`: 0

**Steps**:
1. [Please fill in specific steps, e.g., `GOTO "https://www.example.com"`]
2. [Please fill in specific steps, e.g., `WAIT "domcontentloaded"`]

---

## sample sheet title
**ID**: bfa84
**Type**: process
**Description**: [Describe the first sheet logic, e.g. "enter search query and submit"]
**URL**: `https://www.example.com`
**Locators**: `role=main`, `text="Dashboard"`

**Steps**:
1. [Please fill in specific steps, e.g., `CLICK "role=button[name='Search']"`]
2. [Use semantic selectors, e.g., `INPUT "label=Search" "iPhone"`]
3. [Supported standard actions: GOTO, CLICK, INPUT, HOVER, WAIT, EXTRACT]

---

## sample sheet title 2
**ID**: 99275
**Type**: process
**Description**: [Describe the next sheet logic, e.g. "Process search results and extract data"]
**URL**: `https://www.example.com`
**Locators**: `[Optional]`

**Steps**:
1. [Continue with the next part of the process]

---

## sample delivery title
**ID**: 0dc35
**Type**: delivery
**Description**: Summarize deliverables and end the journey.

**Steps**:
1. [Output final result]
