# Spec 01: 環境設定

## 起始狀態
執行此 spec 前，專案中已有以下檔案：
```
langgraph-workshop/
├── README.md
├── cursor.md
├── requirements.txt    ← 已存在
├── .env                ← 已填好 GOOGLE_API_KEY
└── data/
    ├── __init__.py
    └── restaurants.py
```

## 目標
建立必要的目錄結構，安裝 Python 依賴，驗證 Gemini LLM 可正常呼叫。

---

## 最終目錄結構（此 spec 完成後）

```
langgraph-workshop/
├── README.md
├── cursor.md
├── requirements.txt    ← 已存在，不動
├── .env                ← 已存在，不動
├── data/
│   ├── __init__.py
│   └── restaurants.py
├── graph/              ← 此 spec 建立目錄
│   └── __init__.py     ← 此 spec 建立（空檔案）
├── frontend/           ← 此 spec 建立目錄（空）
└── .venv/              ← 此 spec 建立
```

> `server.py`、`graph/state.py`、`graph/nodes.py`、`graph/router.py`、`graph/main.py`、`frontend/index.html` 由後續 spec 建立。

---

## 步驟一：建立 graph/ 目錄與 __init__.py

```bash
# 建立 graph 目錄並放入空的 __init__.py（使其成為 Python package）
mkdir graph
# 建立空檔案
# Windows PowerShell:
New-Item graph/__init__.py -ItemType File
# macOS / Linux:
touch graph/__init__.py
```

`graph/__init__.py` 內容為**空**，不需要任何程式碼。

## 步驟三：建立 frontend/ 目錄

```bash
mkdir frontend
```

## 步驟三：建立虛擬環境並安裝依賴

```bash
# 建立虛擬環境
python -m venv .venv

# 啟動虛擬環境
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

## 步驟四：確認 .env 格式正確

`.env` 應已存在，格式如下（不需要修改，只確認）：

```
GOOGLE_API_KEY=AIzaSy...（實際的 Key）
```

---

## 驗證

啟動虛擬環境

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

確認虛擬環境已啟動後，執行以下指令，終端機應印出一句中文打招呼：

### 驗證指令 (Windows PowerShell)
```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
import os
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash-lite',
    google_api_key=os.getenv('GOOGLE_API_KEY')
)
r = llm.invoke('說一句中文打招呼')
c = r.content
print(c if isinstance(c, str) else ''.join([x.get('text','') for x in c if isinstance(x,dict) and x.get('type')=='text']))
"
```

### 驗證指令 (Mac OS)
```bash
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash-lite',
    google_api_key=os.getenv('GOOGLE_API_KEY')
)
r = llm.invoke('說一句中文打招呼')
print(r.content)
"
```

✅ 成功：印出中文句子
❌ `ModuleNotFoundError`：虛擬環境未啟動或 `pip install` 未執行
❌ `API key not valid`：`.env` 中的 Key 有誤或格式不對（確認沒有多餘空格）
❌ `GOOGLE_API_KEY` 為 None：`load_dotenv()` 沒讀到 `.env`，確認在專案根目錄執行

## 常見問題

如果api沒有回應，或回應503，請更改使用的模型，換成gemini-3-flash，gemini-2.5-flash，gemini-2.5-flash-lite
