import yaml
import subprocess
import time
import argparse
import sys
import json
import os

# 这是一个 MVP 版本的 "Guide" 程序，负责读取 YAML 并调用 agent-browser
# 目前处于早期开发阶段

class RoadbookGuide:
    def __init__(self, cdp_port=9224):
        self.cdp_port = cdp_port
        self.connected = False

    def connect(self):
        """尝试连接到 agent-browser"""
        print(f"🔗 [Guide] Connecting via agent-browser to port {self.cdp_port}...")
        # 实际实现时，这里可能会启动一个 subprocess 维持连接，或者每次 command 都调用
        # 这里模拟 CLI 调用的方式
        try:
            # 仅作测试，检查 agent-browser 是否存在
            subprocess.run(["agent-browser", "--version"], check=True, capture_output=True)
            self.connected = True
            print("✅ [Guide] agent-browser CLI found.")
        except FileNotFoundError:
            print("❌ [Guide] Error: 'agent-browser' not found in PATH.")
            sys.exit(1)

    def execute_roadbook(self, yaml_path):
        if not self.connected:
            self.connect()

        print(f"📖 [Guide] Loading roadbook: {yaml_path}")
        with open(yaml_path, 'r', encoding='utf-8') as f:
            roadbook = yaml.safe_load(f)

        print(f"🚀 [Guide] Starting mission: {roadbook.get('name')}")
        
        stages = roadbook.get('stages', [])
        for stage in stages:
            print(f"\n🎬 Stage: {stage.get('name')}")
            
            # --- Pre-condition Check (Placeholder) ---
            if 'pre_condition' in stage:
                print(f"  Thinking: Checking environment {stage['pre_condition']}...")
                # TODO: Implement actual check
            
            steps = stage.get('steps', [])
            for step in steps:
                self.execute_step(step)

    def find_element_id(self, landmark):
        """利用真实的 snapshot 输出并在正则层面寻找元素 ID"""
        keyword = landmark.get('keyword', '')
        print(f"     🔍 Taking snapshot to find keyword: '{keyword}'...")
        try:
            result = subprocess.run(["agent-browser", "snapshot"], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"     ❌ agent-browser snapshot failed: {e}")
            return None

        import re
        for line in result.stdout.split('\n'):
            if keyword.lower() in line.lower():
                match = re.search(r'id="(@e\d+)"', line)
                if match:
                    print(f"     🎯 Found target ID: {match.group(1)} in snapshot.")
                    return match.group(1)
        print("     ⚠️ Target not found in snapshot!")
        return None

    def execute_step(self, step):
        step_id = step.get('id')
        intent = step.get('intent')
        action = step.get('action')
        
        print(f"  👉 [{step_id}] Intent: {intent}")
        
        # 真正调用命令行执行
        cmd = []
        if action == 'goto':
            url = step.get('value')
            # 根据真实指令表，网址跳转用 open 命令
            cmd = ["agent-browser", "open", url]
        
        elif action == 'click':
            landmark = step.get('landmark')
            print(f"     Thinking: Locating element with landmark {landmark}...")
            element_id = self.find_element_id(landmark)
            if element_id:
                cmd = ["agent-browser", "click", element_id]
            else:
                print("     ❌ Aborting step due to missing element.")
                return 

        elif action == 'type':
            value = step.get('value')
            landmark = step.get('landmark')
            print(f"     Thinking: Locating element {landmark} to type '{value}'...")
            element_id = self.find_element_id(landmark)
            if element_id:
                cmd = ["agent-browser", "type", element_id, value]
            else:
                print("     ❌ Aborting step due to missing element.")
                return

        elif action == 'wait':
             condition = step.get('condition', '500')
             if condition == 'networkIdle':
                 cmd = ["agent-browser", "wait", "--load", "networkidle"]
             elif condition == 'dom_stable':
                 cmd = ["agent-browser", "wait", "--load", "domcontentloaded"]
        
        if cmd:
            print(f"     ⚡ Executing: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
                time.sleep(1) 
            except subprocess.CalledProcessError as e:
                print(f"     ❌ Command failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roadbook Guide MVP Runner")
    parser.add_argument("roadbook", help="Path to roadbook YAML file")
    args = parser.parse_args()

    guide = RoadbookGuide()
    guide.execute_roadbook(args.roadbook)
