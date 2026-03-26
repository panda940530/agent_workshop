# Spec 06: LLM Prompts

## 目標
定義系統中所有 LLM 呼叫使用的 system prompt 與 user prompt 模板。
此 spec 是 Spec 05 的直接補充——Spec 05 說明「在哪裡使用 prompt」，此 spec 提供「prompt 的完整文字」。

## 使用位置總覽

| Prompt 名稱 | 使用位置 | 類型 |
|---|---|---|
| `parse_input_system` | `parse_input_node` | System Prompt |
| `budget_router_system` | `budget_router` | System Prompt |
| `budget_router_user` | `budget_router` | User Prompt 模板 |
| `recommend_select_system` | `recommend_node`（>3 間時） | System Prompt |
| `recommend_select_user` | `recommend_node`（>3 間時） | User Prompt 模板 |
| `format_response_system` | `format_response_node` | System Prompt |
| `format_response_user` | `format_response_node` | User Prompt 模板 |

---

## Prompt 完整內容

### 1. `parse_input_system`
**用於：** `parse_input_node` 的 SystemMessage

```
你是一個餐廳偏好解析器。請根據使用者的輸入，擷取以下資訊並回傳為純 JSON 格式：
- cuisine_type: "japanese", "italian", "taiwanese", "korean", 或 "thai"
- budget: 預算金額 (整數)。若無則回傳 null
- location: 地點字串。若無則回傳 ""

只能回傳 JSON 字串，不要包含 ```json 標籤或其他文字。
```

**輸入（HumanMessage）：** `state["user_input"]` 直接傳入，不加前綴

**預期回傳：**
```json
{"cuisine_type": "japanese", "budget": 200, "location": ""}
```

**注意：**
- `cuisine_type` 只能是 5 種值之一；LLM 若回傳其他值，`parse_input_node` 的驗證邏輯會 fallback 為 `"taiwanese"`
- 此 prompt 沒有主動引導 LLM 對「酸辣」做泰式聯想；若需要此功能，在 cuisine_type 說明後加入：「若使用者描述酸辣、打拋、咖哩、冬蔭功等特徵，歸類為 thai」

---

### 2. `budget_router_system`
**用於：** `budget_router` 的 SystemMessage

```
綜合考慮使用者的預算金額和語氣來判斷消費意願。
例如「隨便吃 500 元」應歸類為 budget，而「慶祝生日 400 元」也可能應歸類為 premium。
請直接回傳字串 "budget" 或 "premium"，不要有其他文字。
```

### `budget_router_user`
**用於：** `budget_router` 的 HumanMessage

```python
f"使用者輸入: {user_input}\n預算: {budget}"
```

**預期回傳：** 純字串 `budget` 或 `premium`（程式用 `"premium" in content` 判斷）

---

### 3. `recommend_select_system`
**用於：** `recommend_node` 超過 3 間餐廳時的 LLM 篩選

```
你是一個餐廳挑選助手。請從以下餐廳列表中挑選出最適合的 3 間，並以純 JSON 格式回傳這 3 間餐廳的名稱列表，例如: ["餐廳A", "餐廳B", "餐廳C"]。
```

### `recommend_select_user`
**用於：** 對應的 HumanMessage

```python
f"使用者偏好: {json.dumps(prefs, ensure_ascii=False)}\n候選餐廳: {json.dumps(results, ensure_ascii=False)}"
```

**預期回傳：** JSON 陣列，包含 3 個餐廳名稱字串
```json
["築地鮮魚", "鶴橋拉麵", "隱家日式料理"]
```

**注意：** `_extract_json` 解析後得到 `list[str]`，程式用 `r["name"] in selected_names` 過濾

---

### 4. `format_response_system`
**用於：** `format_response_node` 的 SystemMessage

```
你是一個專業的美食推薦助理。請用繁體中文、自然且有溫度的語氣向使用者介紹餐廳。
介紹內容需包含餐廳名稱、地點、價格、評分、特色，並適當加上 emoji 讓語意生動。
```

### `format_response_user`
**用於：** 對應的 HumanMessage

```python
f"使用者需求: {state.get('user_input', '')}\n精選推薦餐廳清單: {json.dumps(recs, ensure_ascii=False)}\n請幫我撰寫一段推薦文。"
```

**預期回傳：** 繁體中文多段推薦文字，包含 emoji

---

## 調整指引

### 想讓 LLM 更準確識別特定料理
在 `parse_input_system` 的 cuisine_type 說明後加入聯想提示：

```
- "thai": 包含打拋、冬蔭功、泰式咖哩、酸辣等描述
- "japanese": 包含壽司、拉麵、丼飯、居酒屋等描述
```

### 想改變路由邏輯
修改 `budget_router_system`，例如調整「預算 300 以下傾向 budget」的門檻說明。

### 想改變推薦文風格
修改 `format_response_system`，例如改為「簡短條列式」或「加入推薦理由」。

---

## 注意事項

- 所有 prompt 中提到「不要 markdown」或「只回傳 JSON」時，仍然要搭配 `_extract_json` 的 fence 處理，因為 LLM 偶爾會忽略指示。
- `parse_input_system` 特別說明「不要包含 \`\`\`json 標籤」，但 `_extract_json` 依然可以處理有 fence 的情況，所以不會造成問題。
