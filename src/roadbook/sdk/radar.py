import json
from typing import List, Dict, Any
from playwright.sync_api import Page

class Radar:
    """
    Radar (雷达扫描) 工具：
    基于 Agent Browser 的思路，利用 page.evaluate() 注入 JavaScript
    来快速提取页面上可见的、非禁用的核心交互元素、文本内容、表格以及下载链接。
    帮助 Agent 快速定位可操作目标，避免盲目尝试。
    """
    def __init__(self, page: Page):
        self.page = page

    def scan_interactive_elements(self) -> List[Dict[str, Any]]:
        """
        扫描页面上的核心交互元素（按钮、链接、输入框、下拉框等）。
        过滤掉不可见（隐藏、尺寸为 0）和禁用的元素。
        返回包含标签名、文本、属性、位置信息的字典列表。
        """
        js_code = """
        () => {
            const isVisible = (el) => {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };

            const isInteractive = (el) => {
                if (el.disabled) return false;
                // 对于 a 标签，最好有 href 或者是具有点击事件的元素（这里通过标签名和 role 粗略判断）
                return true;
            };

            const elements = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="menuitem"]'));
            
            const results = [];
            let index = 0;
            for (const el of elements) {
                if (isVisible(el) && isInteractive(el)) {
                    const rect = el.getBoundingClientRect();
                    const tagName = el.tagName.toLowerCase();
                    
                    // 提取核心文本
                    let text = el.innerText || el.textContent || '';
                    if (tagName === 'input' && (el.type === 'submit' || el.type === 'button')) {
                        text = el.value || text;
                    } else if (tagName === 'input' || tagName === 'textarea') {
                        text = el.placeholder || el.name || text;
                    }
                    
                    text = text.trim().replace(/\\s+/g, ' ');

                    // 提取关键属性
                    const attributes = {};
                    if (el.id) attributes.id = el.id;
                    if (el.name) attributes.name = el.name;
                    if (el.href) attributes.href = el.href;
                    if (el.type) attributes.type = el.type;
                    
                    const ariaLabel = el.getAttribute('aria-label');
                    if (ariaLabel) attributes['aria-label'] = ariaLabel;

                    // 精简：如果没有文本且没有 aria-label、title 等，可能是一个无意义的占位符（视情况保留）
                    if (!text && !ariaLabel && !el.title && tagName !== 'input') {
                        // 尝试查找内部的 SVG 或 img
                        if (!el.querySelector('svg, img')) {
                            continue; // 跳过完全没有意义的元素
                        }
                    }

                    results.push({
                        index: index++,
                        tag: tagName,
                        text: text.substring(0, 100), // 限制文本长度
                        attributes: attributes,
                        rect: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    });
                }
            }
            return results;
        }
        """
        return self.page.evaluate(js_code)

    def scan_content(self) -> List[Dict[str, Any]]:
        """
        扫描页面的核心文本内容块（标题、段落、文章区域）。
        """
        js_code = """
        () => {
            const isVisible = (el) => {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };

            const elements = Array.from(document.querySelectorAll('h1, h2, h3, h4, p, article, section'));
            const results = [];
            for (const el of elements) {
                if (isVisible(el)) {
                    const text = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
                    if (text.length > 10) { // 过滤掉太短的无意义文本
                        results.push({
                            tag: el.tagName.toLowerCase(),
                            text: text.substring(0, 500) // 截取前 500 个字符
                        });
                    }
                }
            }
            // 简单去重和嵌套过滤可以进一步优化，这里返回平铺的块
            return results;
        }
        """
        return self.page.evaluate(js_code)

    def scan_tables(self) -> List[Dict[str, Any]]:
        """
        扫描页面上的表格内容，返回结构化的表格数据。
        """
        js_code = """
        () => {
            const tables = Array.from(document.querySelectorAll('table'));
            const results = [];
            for (let i = 0; i < tables.length; i++) {
                const table = tables[i];
                // 检查是否可见
                const rect = table.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;

                const tableData = {
                    index: i,
                    headers: [],
                    rows: []
                };

                // 提取表头
                const headers = table.querySelectorAll('th');
                headers.forEach(th => {
                    tableData.headers.push((th.innerText || th.textContent || '').trim().replace(/\\s+/g, ' '));
                });

                // 提取数据行
                const rows = table.querySelectorAll('tr');
                rows.forEach(tr => {
                    const cells = tr.querySelectorAll('td');
                    if (cells.length > 0) {
                        const rowData = Array.from(cells).map(td => (td.innerText || td.textContent || '').trim().replace(/\\s+/g, ' '));
                        // 过滤掉完全空的数据行
                        if (rowData.some(cell => cell.length > 0)) {
                            tableData.rows.push(rowData);
                        }
                    }
                });

                if (tableData.rows.length > 0 || tableData.headers.length > 0) {
                    results.push(tableData);
                }
            }
            return results;
        }
        """
        return self.page.evaluate(js_code)

    def scan_downloads(self, extensions: List[str] = None) -> List[Dict[str, Any]]:
        """
        扫描页面上的下载链接。
        通过匹配 href 后缀或 download 属性来识别。
        """
        if not extensions:
            extensions = ['.pdf', '.zip', '.rar', '.tar', '.gz', '.csv', '.xlsx', '.xls', '.docx', '.doc', '.png', '.jpg']
            
        js_code = """
        (extensions) => {
            const links = Array.from(document.querySelectorAll('a'));
            const results = [];
            
            for (const link of links) {
                const href = link.href || '';
                const hasDownloadAttr = link.hasAttribute('download');
                
                let isDownload = hasDownloadAttr;
                if (!isDownload && href) {
                    const lowerHref = href.toLowerCase();
                    isDownload = extensions.some(ext => lowerHref.endsWith(ext) || lowerHref.includes(ext + '?'));
                }
                
                if (isDownload) {
                    const text = (link.innerText || link.textContent || '').trim().replace(/\\s+/g, ' ');
                    results.push({
                        text: text || link.getAttribute('download') || 'Unknown',
                        href: href,
                        is_explicit_download: hasDownloadAttr
                    });
                }
            }
            return results;
        }
        """
        return self.page.evaluate(js_code, extensions)

    def scan_hoverable_elements(self) -> List[Dict[str, Any]]:
        """
        扫描页面上可能支持 hover 交互的元素（如下拉菜单、Tooltip、浮窗等）。
        基于 ARIA 属性、常见类名 (dropdown, tooltip 等)、title 属性以及内联事件来做启发式探测。
        """
        js_code = """
        () => {
            const results = [];
            let index = 0;
            const isVisible = (el) => {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };

            // 启发式选择器：寻找具有提示或展开菜单特征的元素
            const selectors = [
                '[title]', '[data-tooltip]', '[data-bs-toggle="tooltip"]', '[data-toggle="tooltip"]',
                '[aria-haspopup]', '[data-hover]', '.dropdown', '.dropdown-toggle', '.menu-item', 
                '.has-tooltip', '[onmouseover]', '[onmouseenter]'
            ].join(', ');

            const elements = Array.from(document.querySelectorAll(selectors));
            const seen = new Set();

            for (const el of elements) {
                if (isVisible(el) && !seen.has(el)) {
                    seen.add(el);
                    const rect = el.getBoundingClientRect();
                    const tagName = el.tagName.toLowerCase();
                    let text = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ').substring(0, 100);
                    
                    // 判断它为什么被认为是 hoverable
                    let reasons = [];
                    if (el.hasAttribute('title')) reasons.push('title');
                    if (el.hasAttribute('aria-haspopup')) reasons.push('aria-haspopup');
                    if (el.hasAttribute('onmouseover') || el.hasAttribute('onmouseenter')) reasons.push('js-event');
                    if (el.className && typeof el.className === 'string' && el.className.match(/(dropdown|tooltip|popover|menu)/i)) reasons.push('class-heuristic');
                    if (el.hasAttribute('data-tooltip') || el.hasAttribute('data-toggle') || el.hasAttribute('data-bs-toggle')) reasons.push('data-attr-heuristic');

                    results.push({
                        index: index++,
                        tag: tagName,
                        text: text,
                        reasons: reasons,
                        rect: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    });
                }
            }
            return results;
        }
        """
        return self.page.evaluate(js_code)

    def scan_scrollable_areas(self) -> List[Dict[str, Any]]:
        """
        扫描页面上具有内部滚动条的容器（不包括整页滚动）。
        有助于 Agent 发现需要滚动才能加载更多（Infinite Scroll）或查看隐藏内容的区域。
        """
        js_code = """
        () => {
            const results = [];
            let index = 0;
            // 针对常见的块级容器进行检测，避免遍历所有元素导致性能问题
            const elements = Array.from(document.querySelectorAll('div, main, section, aside, ul, tbody, nav'));
            
            for (const el of elements) {
                if (el === document.documentElement || el === document.body) continue;
                
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;

                const style = window.getComputedStyle(el);
                const isScrollableY = (style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight;
                const isScrollableX = (style.overflowX === 'auto' || style.overflowX === 'scroll') && el.scrollWidth > el.clientWidth;

                if (isScrollableY || isScrollableX) {
                    results.push({
                        index: index++,
                        tag: el.tagName.toLowerCase(),
                        id: el.id || '',
                        className: el.className || '',
                        scroll_y: isScrollableY,
                        scroll_x: isScrollableX,
                        rect: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    });
                }
            }
            return results;
        }
        """
        return self.page.evaluate(js_code)

    def scan_draggable_elements(self) -> List[Dict[str, Any]]:
        """
        扫描页面上声明了 draggable="true" 的元素，支持拖拽交互。
        """
        js_code = """
        () => {
            const results = [];
            let index = 0;
            const elements = Array.from(document.querySelectorAll('[draggable="true"]'));
            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) continue;
                
                let text = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ').substring(0, 100);
                results.push({
                    index: index++,
                    tag: el.tagName.toLowerCase(),
                    text: text,
                    rect: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                });
            }
            return results;
        }
        """
        return self.page.evaluate(js_code)

    def scan_all(self) -> Dict[str, Any]:
        """
        综合扫描：返回页面所有关键信息的快照。
        """
        return {
            "interactive_elements": self.scan_interactive_elements(),
            "hoverable_elements": self.scan_hoverable_elements(),
            "scrollable_areas": self.scan_scrollable_areas(),
            "draggable_elements": self.scan_draggable_elements(),
            "content": self.scan_content(),
            "tables": self.scan_tables(),
            "downloads": self.scan_downloads()
        }
