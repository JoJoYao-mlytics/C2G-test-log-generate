# CDN 去重測試執行時機指南

## 🕐 **腳本執行時機說明**

### **動態時間調整機制**
`generate_dedup_test_logs.py` 使用動態時間生成，每次執行都會：
- 基準時間 = 當前時間 - 30分鐘
- 處理窗口 = 基準時間 ~ 基準時間 + 2小時
- 確保所有生成的日誌都在 Log Processor 的處理範圍內

### **執行時機範例**

#### **今天執行 (2025-09-10 15:26:12)**
```
⏰ 基準時間：2025-09-10 14:56:12
🕐 處理窗口：14:56:12 ~ 16:56:12
📊 日誌時間戳：10/Sep/2025:15:05:12 開始
```

#### **明天執行 (2025-09-11 15:28:17)**
```
⏰ 基準時間：2025-09-11 14:58:17
🕐 處理窗口：14:58:17 ~ 16:58:17  
📊 日誌時間戳：11/Sep/2025:14:58:17 開始
```

## 📋 **測試執行建議**

### **1. 立即測試 (推薦)**
```bash
# 生成並立即執行測試
python3 generate_dedup_test_logs.py
# 立即上傳到 S3 並啟動 Log Processor
```
**優點：** 時間戳最新，處理窗口充足

### **2. 延後測試**
```bash
# 任何時候重新生成
python3 generate_dedup_test_logs.py
# 腳本會自動調整為當前最佳時間
```
**優點：** 靈活性高，自動適應

### **3. 定時測試**
```bash
# 設定 cron job 每天執行
0 14 * * * cd /path/to/logs && python3 generate_dedup_test_logs.py
```
**優點：** 自動化，持續驗證

## ⚠️ **特殊測試情況**

### **TTL 真實過期測試**

**方法 1：分批執行**
```bash
# 第一批：生成並處理
python3 generate_dedup_test_logs.py
# 上傳 test_logs_ttl_boundary_batch1.log

# 等待 2+ 小時後
# 第二批：重新生成當前時間的第二批
# 手動修改腳本或使用第二批檔案
```

**方法 2：手動調整 Redis TTL**
```bash
# 設定短 TTL 進行快速測試
redis-cli CONFIG SET timeout 300  # 5分鐘 TTL
```

### **並發測試最佳時機**
```bash
# 確保所有處理器同時執行
python3 generate_dedup_test_logs.py
# 同時啟動 5 個 Log Processor 實例
```

## 🎯 **時間戳驗證檢查**

### **執行前檢查**
```bash
# 檢查當前時間
date

# 檢查生成的時間戳範圍
python3 -c "
from datetime import datetime, timedelta
now = datetime.now()
base = now - timedelta(minutes=30)
print(f'處理窗口: {base.strftime(\"%H:%M\")} ~ {(base + timedelta(hours=2)).strftime(\"%H:%M\")}')
"
```

### **執行後驗證**
```bash
# 檢查生成檔案的時間戳
head -10 test_logs_basic_dedup_full.log | grep -o '"[0-9][0-9]/[A-Z][a-z][a-z]/[0-9][0-9][0-9][0-9]:[0-9][0-9]:[0-9][0-9]:[0-9][0-9]'

# 確認在處理窗口內
python3 -c "
from datetime import datetime
import re

with open('test_logs_basic_dedup_full.log', 'r') as f:
    content = f.read()
    
timestamps = re.findall(r'\"(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})', content)
if timestamps:
    first_ts = datetime.strptime(timestamps[0], '%d/%b/%Y:%H:%M:%S')
    print(f'第一筆記錄時間: {first_ts}')
    print(f'當前時間: {datetime.now()}')
    diff = datetime.now() - first_ts
    print(f'時間差: {diff.total_seconds()/3600:.1f} 小時')
    if diff.total_seconds() < 7200:  # 2小時
        print('✅ 在處理窗口內')
    else:
        print('❌ 超出處理窗口')
"
```
## **產出檔案說明**
| 檔案名稱 | 大小 | 用途 |
|----------|----------|----------|
| test_logs_basic_dedup_full.log | 513KB | 基礎去重測試 |
| test_logs_concurrent_processor1_full.log | 511KB | 並發去重測試 |
| test_logs_high_frequency_dedup_full.log | 5.6MB | 高頻重複測試 |
| test_logs_ttl_boundary_batch1.log | 53KB | TTL 邊界測試 |

## 📊 **不同時機執行的影響**

| 執行時機 | 處理窗口 | 測試效果 | 建議使用 |
|----------|----------|----------|----------|
| 立即執行 | 充足 (1.5-2小時) | ✅ 最佳 | 正式測試 |
| 1小時後 | 適中 (0.5-1.5小時) | ✅ 良好 | 補充測試 |
| 2小時後 | 需重新生成 | ⚠️ 需更新 | 重新生成 |
| 隔天執行 | 自動調整 | ✅ 良好 | 日常測試 |

## 🚀 **最佳實務建議**

1. **測試前生成** - 在開始測試前才執行腳本
2. **驗證時間戳** - 確認生成的時間戳在處理窗口內  
3. **保留彈性** - 隨時可重新生成適應當前時間
4. **記錄執行時間** - 在測試報告中記錄生成和執行時間

這樣的設計確保了測試的時效性和可重複性！
