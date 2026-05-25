## 爬虫处理流程（SOP）

### 1. 起始 URL（start_url）
- **作用**：爬虫的入口点，通常是商品列表的第一页或分类页。
- **产出**：从中提取出**分页面 URL（index_url）**，即需要依次遍历的列表页链接。

---

### 2. 分页面 URL（index_url）
- **来源**：从 start_url 解析得到，可能是通过翻页规则生成的多个 URL（如 `page=1`、`page=2`...）。
- **作用**：每个 index_url 对应一页商品列表，用于获取该页中所有商品的**单品页链接（shangpin_1_url）**。

---

### 3. 单品页 URL（shangpin_1_url）
- **来源**：从 index_url 的 HTML 中提取（例如通过 CSS 选择器获取商品详情页的 `<a>` 标签）。
- **作用**：访问该页面，获取：
  - 商品的基础信息（价格、版本、名称等）
  - 用于后续 Ajax 请求的 `proId`
  - 可能直接跳转到参数页（param_url），也可能需要先请求 Ajax 接口来获取不同版本的商品链接。

---

### 4. Ajax 中转 URL（Ajax_url）
- **构造**：`https://detail.zol.com.cn/xhr5_Product_GetProSkuInfo_proId=1974243.html`
  - 其中 `proId` 从上一步的单品页中提取。
- **作用**：发送请求获取该商品所有**具体版本（如不同配置、颜色）**的详细信息，包括：
  - 每个版本的 `proUrl`（即 `shangpin_2_url`）
  - `skuId`
  - 价格、版本描述等
- **为什么需要这一步**：有些商品页面会列出多个配置（如不同硬盘、内存大小），直接获取 Ajax 接口可以避免解析复杂的 HTML 结构。

---

### 5. 具体版本 URL（shangpin_2_url）
- **来源**：从 Ajax 接口返回的 JSON 中提取 `proUrl`（例如 `/notebook/index2139965.shtml`）。
- **作用**：访问该 URL 获取该具体版本的：
  - 最终价格
  - 详细规格参数链接（`param_url`）
  - 其他版本字段（如“皓月银”、“i5 13420H/16GB/512GB”等）

---

### 6. 参数页 URL（param_url）
- **来源**：从 `shangpin_2_url` 的 HTML 或直接从该页面上提取“详细参数”的链接（通常包含 `param.shtml`）。
- **作用**：获取商品的所有详细参数（CPU、内存、屏幕、重量等），这也是最终要存储的数据。

---

## 数据流向总结（文字链）

```
start_url
  └─> 生成 index_url 列表
        └─> 每个 index_url 解析出 shangpin_1_url
              └─> 每个 shangpin_1_url 提取 proId
                    └─> 拼接 Ajax_url，获取多个 shangpin_2_url
                          └─> 每个 shangpin_2_url 提取 param_url
                                └─> 解析 param_url 里的详细参数并存储
```

---

## 流程关键点说明

- **为什么要分这么多层**：因为中关村在线的商品数据结构是分层嵌套的：
  - 列表页 → 系列页（可能包含多个配置） → 详细参数页。
  - 直接爬到参数页需要先知道具体哪个 `proId` 属于哪个配置，因此 Ajax 接口是必要的桥梁。
- **翻页控制**：`index_url` 通常包含页码参数，可以通过循环或递归请求所有页的列表。
- **去重**：如果同一商品的不同版本共享相同的 `param_url`，需要在存储时做去重（例如用 `param_url` 或 `proId` 作为唯一键）。