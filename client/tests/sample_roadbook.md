---
id: "rb-amazon-checkout-v1"
name: "Amazon Checkout"
version: "4.0"
owner: "user_123"
platform: "desktop"
locale: "zh-CN"
region: "CN"
description: "在亚马逊上搜索商品并完成下单流程"
inputs:
  keyword: "搜索关键词"
  max_price: "最高价格限制"
outputs:
  order_id: "订单编号"
  total_amount: "总金额"
---

## 启动与搜索
**ID**: a1b2
**Description**: 打开亚马逊主页并搜索指定商品。
**URL**: `https://www.amazon.cn`

**Steps**:
1. GOTO "https://www.amazon.cn"
2. INPUT "#twotabsearchtextbox" "{keyword}"
3. CLICK "#nav-search-submit-button"
4. WAIT "networkidle"

---

## 列表页定位
**ID**: 3c4d
**Description**: 确认已进入搜索结果页。
**URL**: `s?k=`
**Locators**: `text="结果"`, `.s-result-list`

---

## 选择商品
**ID**: 5e6f
**Description**: 从列表中选择第一个符合价格要求的商品。
**Reference**: ![Target Product Example](./assets/product_example.png)

**Steps**:
1. WAIT ".s-result-item"
2. CLICK ".s-result-item:has-text('{price}') img"

---

## 详情页验证
**ID**: 7g8h
**Description**: 验证是否成功进入商品详情页且商品有货。

**Assertions**:
- [ ] 页面标题包含商品名称
- [ ] 存在 "加入购物车" 按钮 (`#add-to-cart-button`)
- [ ] 价格显示正常

---

## 结账
**ID**: 9i0j
**Description**: 将商品加入购物车并完成下单。

**Steps**:
1. CLICK "#add-to-cart-button"
2. WAIT 2000
3. CLICK "input[name='proceedToRetailCheckout']"
