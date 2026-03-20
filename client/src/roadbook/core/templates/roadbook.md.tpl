---
id: "{rb_id}"
name: "{name}"
version: "1.0"
owner: "user"
platform: "desktop"
description: "{description}"
entry_url: "{entry_url}"
tags: []
inputs: 
  sample_param: "example_value"
outputs: {}
---

## sample initialization title
**ID**: init
**Type**: setup
**Description**: Verify browser environment (connection method) and authentication state.
**URL**: `{entry_url}`
**Locators**: `body`

**Steps**:
1. [Please fill in specific steps, e.g., `GOTO "{entry_url}"`]
2. [Please fill in specific steps, e.g., `WAIT "domcontentloaded"`]

---

## sample sheet title
**ID**: process_sheet_1
**Type**: process
**Description**: [Describe the first sheet logic, e.g. "enter search query and submit"]
**URL**: `{entry_url}`
**Locators**: `role=main`, `text="Dashboard"`

**Steps**:
1. [Please fill in specific steps, e.g., `CLICK "role=button[name='Search']"`]
2. [Use semantic selectors, e.g., `INPUT "label=Search" "iPhone"`]
3. [Supported standard actions: GOTO, CLICK, INPUT, HOVER, WAIT, EXTRACT]

---

## sample sheet title 2
**ID**: process_sheet_2
**Type**: process
**Description**: [Describe the next sheet logic, e.g. "Process search results and extract data"]
**URL**: `{entry_url}`
**Locators**: `[Optional]`

**Steps**:
1. [Continue with the next part of the process]

---

## sample delivery title
**ID**: delivery
**Type**: delivery
**Description**: Summarize deliverables and end the journey.

**Steps**:
1. [Output final result]
