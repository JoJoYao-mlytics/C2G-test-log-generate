# CDN 日誌產生器

根據 Gcore CDN 存取日誌格式，產生大量唯一且不重複的測試資料。

## 特色功能

- ✅ **確保唯一性**: 所有產生的記錄都是唯一的，避免重複
- ✅ **可變數控制**: 資料筆數、時間等都可以用變數帶入
- ✅ **真實格式**: 完全符合原始 CDN 日誌格式
- ✅ **大量資料支援**: 支援產生數萬甚至數十萬筆記錄
- ✅ **批次處理**: 自動分批處理，避免記憶體問題
- ✅ **多樣化內容**: 自動產生多種檔案類型、IP 地址、User-Agent 等

## 安裝需求

```bash
# Python 3.7 或更高版本
python3 --version

# 無需額外套件，使用標準庫
```

## 快速開始

### 1. 命令列使用

```bash
# 基本使用 - 產生 1000 筆記錄
python3 cdn_log_generator.py 1000

# 指定開始時間和輸出檔案
python3 cdn_log_generator.py 5000 \
  --start-time "22/Aug/2025:10:00:00 +0000" \
  --output test_logs.log \
  --verbose

# 產生大量資料（10萬筆）
python3 cdn_log_generator.py 100000 \
  --start-time "23/Aug/2025:00:00:00 +0000" \
  --interval 0.1 \
  --output large_dataset.log \
  --batch-size 5000 \
  --verbose
```

### 2. 程式中使用

```python
from cdn_log_generator import generate_cdn_logs

# 簡單使用
logs = generate_cdn_logs(
    count=1000,
    start_time_str="22/Aug/2025:15:00:00 +0000",
    interval=0.5,
    output_file="my_logs.log"
)

print(f"產生了 {len(logs)} 筆記錄")
```

### 3. 變數驅動配置

```python
# 所有參數都用變數控制
RECORD_COUNT = 50000
START_TIME = "25/Aug/2025:09:30:00 +0000"
INTERVAL_SECONDS = 0.2
OUTPUT_FILE = f"cdn_logs_{RECORD_COUNT}.log"

logs = generate_cdn_logs(
    count=RECORD_COUNT,
    start_time_str=START_TIME,
    interval=INTERVAL_SECONDS,
    output_file=OUTPUT_FILE
)
```

## 參數說明

### 命令列參數

| 參數 | 簡寫 | 類型 | 預設值 | 說明 |
|------|------|------|--------|------|
| `count` | - | int | 1000 | 要產生的記錄數量 |
| `--start-time` | `-s` | str | "21/Aug/2025:15:05:11 +0000" | 開始時間 |
| `--interval` | `-i` | float | 1.0 | 時間間隔（秒） |
| `--output` | `-o` | str | - | 輸出檔案路徑 |
| `--batch-size` | `-b` | int | 10000 | 批次處理大小 |
| `--verbose` | `-v` | flag | False | 顯示詳細進度 |

### 時間格式

時間必須使用以下格式：`DD/MMM/YYYY:HH:MM:SS +0000`

範例：
- `21/Aug/2025:15:05:11 +0000`
- `01/Jan/2025:00:00:00 +0000`
- `31/Dec/2024:23:59:59 +0000`

## 使用範例

### 範例 1: 基本測試資料

```bash
# 產生 100 筆測試記錄
python3 cdn_log_generator.py 100 \
  --start-time "22/Aug/2025:10:00:00 +0000" \
  --output basic_test.log
```

### 範例 2: 高頻率資料

```bash
# 產生高頻率資料（每 0.1 秒一筆）
python3 cdn_log_generator.py 10000 \
  --start-time "22/Aug/2025:14:00:00 +0000" \
  --interval 0.1 \
  --output high_frequency.log \
  --verbose
```

### 範例 3: 大量資料集

```bash
# 產生 50 萬筆記錄
python3 cdn_log_generator.py 500000 \
  --start-time "23/Aug/2025:00:00:00 +0000" \
  --interval 0.05 \
  --output massive_dataset.log \
  --batch-size 10000 \
  --verbose
```

### 範例 4: 程式化使用

```python
from cdn_log_generator import CDNLogGenerator
import datetime

# 建立產生器
generator = CDNLogGenerator()

# 產生特定時間範圍的資料
start_time = datetime.datetime(2025, 8, 22, 15, 0, 0)
logs = generator.generate_logs(start_time, 1000, 0.5)

# 檢查唯一性
print(f"產生記錄: {len(logs)}")
print(f"唯一客戶端 ID: {len(generator.used_client_ids)}")
print(f"唯一追蹤 ID: {len(generator.used_trace_ids)}")
print(f"唯一組合: {len(generator.used_combinations)}")
```

## 資料格式說明

產生的日誌格式完全符合原始 CDN 日誌，包含以下欄位：

1. **時間戳記**: `"21/Aug/2025:15:05:11 +0000"`
2. **HTTP 方法**: `"GET"`
3. **協定**: `"http"`
4. **域名**: `"cdn-aliyun-hw-mc.aki-game.net"`
5. **請求路徑**: `/prod/client/...`
6. **完整請求**: `"GET /path HTTP/1.1"`
7. **狀態碼**: `"200"`, `"404"`, `"500"` 等
8. **回應時間**: `"0.009207"`
9. **請求大小**: `"686"`
10. **回應大小**: `"1494"`
11. **快取狀態**: `"HIT"`, `"MISS"` 等
12. **客戶端 IP**: IPv4 或 IPv6 地址
13. **伺服器 IP**: `"45.82.103.8"`
14. **連接埠**: `"80"`
15. **內容類型**: `"application/json"` 等
16. **User-Agent**: 各種客戶端標識
17. **追蹤 ID**: 唯一的請求追蹤識別碼
18. **其他欄位**: 各種統計和元資料

## 唯一性保證

本產生器確保以下唯一性：

- **客戶端 ID**: 每個都是唯一的 32 字元識別碼
- **追蹤 ID**: 每個請求都有唯一的追蹤識別碼
- **IP 地址**: 動態產生大量不同的 IP 地址
- **組合鍵**: 時間+路徑+IP+追蹤ID 的組合確保記錄唯一性

## 效能考量

- **記憶體使用**: 使用批次處理避免記憶體不足
- **處理速度**: 每秒可產生數千筆記錄
- **檔案大小**: 每筆記錄約 500-800 字元
- **唯一性檢查**: 使用集合（set）快速檢查重複

## 故障排除

### 常見問題

1. **時間格式錯誤**
   ```
   錯誤: 無法解析時間格式
   解決: 確保使用正確格式 DD/MMM/YYYY:HH:MM:SS +0000
   ```

2. **記憶體不足**
   ```
   解決: 減少 batch-size 參數或分批產生
   ```

3. **檔案權限問題**
   ```
   解決: 確保輸出目錄有寫入權限
   ```

### 效能調優

- 大量資料時使用 `--batch-size` 控制記憶體使用
- 使用 `--verbose` 監控進度
- 調整 `--interval` 控制資料密度

## 授權

此工具僅供測試和開發使用。
