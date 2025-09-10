#!/usr/bin/env python3
"""
CDN 日誌去重測試資料生成器
基於 sample.log 格式生成各種去重測試場景的日誌檔案
"""

import hashlib
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

class CDNLogGenerator:
    def __init__(self):
        # 使用當前時間作為基準，確保在 Log Processor 的 2 小時處理窗口內
        current_time = datetime.now()
        # 設定為當前時間往前 30 分鐘，確保在處理窗口內且有足夠時間執行測試
        self.base_timestamp = current_time - timedelta(minutes=30)
        self.client_ips = [
            "2803:c600:9101:8144:1f7:a15:21a6:981",
            "181.43.228.197",
            "138.84.62.153", 
            "64.76.142.75",
            "179.60.74.234",
            "200.104.214.144",
            "191.115.105.54",
            "186.11.13.107",
            "186.40.96.82",
            "38.51.244.94"
        ]
        self.paths = [
            "/prod/client/Windows/KeyList_2.5.0.json",
            "/prod/client/Android/PreDownload.json", 
            "/prod/client/IOS/VideoConfig.json",
            "/prod/client/Windows/pakchunk0-WindowsNoEditor_P.pak",
            "/prod/client/Android/GameConfig.json",
            "/prod/client/IOS/AssetBundle.pak"
        ]
        self.user_agents = [
            "Client/++UE4+Release-4.26-CL-144272156 Windows/10.0.26100.1.256.64bit",
            "Client/++UE4+Release-4.26-CL-142563600 Android/14",
            "Client/++UE4+Release-4.26-CL-142563677 IOS/18.5",
            "Client/++UE4+Release-4.26-CL-142563600 Android/15"
        ]

    def generate_trace_id(self, unique_suffix: str = None) -> str:
        """生成追蹤ID"""
        if unique_suffix:
            return f"00-{unique_suffix}-{uuid.uuid4().hex[:16]}-01"
        return f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01"

    def generate_dedup_key(self, trace_id: str, timestamp: str, client_ip: str, path: str) -> str:
        """生成去重鍵 (MD5)"""
        key_string = f"{trace_id}{timestamp}{client_ip}{path}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def generate_log_entry(self, timestamp: datetime, path: str, client_ip: str, 
                          trace_id: str, response_size: int = 1494) -> str:
        """生成單筆日誌記錄 - 包含明顯測試標識"""
        timestamp_str = timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")
        
        # 添加測試標識的 User-Agent
        base_user_agent = random.choice(self.user_agents)
        test_user_agent = f"TestClient-DEDUP-QA/{base_user_agent}"
        
        # 測試專用主機名
        test_hostname = "cdn-test-dedup-qa.aki-game.net"
        
        # 測試專用路徑前綴
        test_path = f"/test-dedup{path}" if not path.startswith("/test-dedup") else path
        
        return f'"{timestamp_str}" "GET" "http" "{test_hostname}" "{test_path}" "GET {test_path} HTTP/1.1" "200" "{random.uniform(0.001, 1.0):.6f}" "{random.randint(600, 700)}" "{response_size}" "HIT" "{client_ip}" "45.82.103.8" "80" "-" "application/json" "{test_user_agent}" "{trace_id}" "{random.randint(10000, 50000)}" "{random.randint(25, 500)}" "{random.randint(25, 500)}" "-" "{client_ip}" "CL" "HTTP/1.1" "-" "Tue, 12 Aug 2025 13:28:00 GMT" "-" "{random.uniform(0.001, 1.0):.6f}"'

    def generate_basic_dedup_logs(self, total_records: int = 1000, duplicate_rate: float = 0.3) -> List[str]:
        """生成基礎去重測試日誌"""
        logs = []
        unique_count = int(total_records * (1 - duplicate_rate))
        duplicate_count = total_records - unique_count
        
        # 生成唯一記錄
        unique_logs = []
        for i in range(unique_count):
            timestamp = self.base_timestamp + timedelta(seconds=i*5)
            path = random.choice(self.paths)
            client_ip = random.choice(self.client_ips)
            trace_id = self.generate_trace_id(f"unique-{i:06d}")
            
            log_entry = self.generate_log_entry(timestamp, path, client_ip, trace_id)
            unique_logs.append(log_entry)
            logs.append(log_entry)
        
        # 生成重複記錄
        for i in range(duplicate_count):
            # 隨機選擇一筆唯一記錄進行重複
            duplicate_log = random.choice(unique_logs)
            logs.append(duplicate_log)
        
        # 打亂順序模擬真實情況
        random.shuffle(logs)
        return logs

    def generate_concurrent_dedup_logs(self, processor_id: int, total_records: int = 1000, 
                                     shared_rate: float = 0.5) -> List[str]:
        """生成並發去重測試日誌"""
        logs = []
        shared_count = int(total_records * shared_rate)
        unique_count = total_records - shared_count
        
        # 生成共享記錄 (會在多個處理器中出現)
        for i in range(shared_count):
            timestamp = self.base_timestamp + timedelta(seconds=i*3)
            path = f"/prod/client/shared/asset-{i%10:03d}.json"
            client_ip = self.client_ips[i % len(self.client_ips)]
            trace_id = self.generate_trace_id(f"shared-{i:06d}")
            
            log_entry = self.generate_log_entry(timestamp, path, client_ip, trace_id)
            logs.append(log_entry)
        
        # 生成處理器獨有記錄
        for i in range(unique_count):
            timestamp = self.base_timestamp + timedelta(seconds=(shared_count + i)*3)
            path = f"/prod/client/processor{processor_id}/asset-{i:06d}.json"
            client_ip = random.choice(self.client_ips)
            trace_id = self.generate_trace_id(f"proc{processor_id}-{i:06d}")
            
            log_entry = self.generate_log_entry(timestamp, path, client_ip, trace_id)
            logs.append(log_entry)
        
        return logs

    def generate_high_frequency_dedup_logs(self, total_records: int = 10000, 
                                         duplicate_rate: float = 0.9) -> List[str]:
        """生成高頻重複測試日誌"""
        logs = []
        unique_count = int(total_records * (1 - duplicate_rate))
        
        # 生成熱門資源記錄 (會被大量重複)
        hot_timestamp = self.base_timestamp
        hot_path = "/prod/client/hot/popular-game-asset.pak"
        hot_client_ip = self.client_ips[0]
        hot_trace_id = self.generate_trace_id("hot-asset-repeated")
        
        hot_log = self.generate_log_entry(hot_timestamp, hot_path, hot_client_ip, 
                                        hot_trace_id, response_size=110851647)
        
        # 生成唯一記錄
        for i in range(unique_count):
            if i == 0:
                # 第一筆是熱門資源
                logs.append(hot_log)
            else:
                timestamp = self.base_timestamp + timedelta(seconds=i*2)
                path = f"/prod/client/unique/asset-{i:06d}.json"
                client_ip = random.choice(self.client_ips)
                trace_id = self.generate_trace_id(f"unique-{i:06d}")
                
                log_entry = self.generate_log_entry(timestamp, path, client_ip, trace_id)
                logs.append(log_entry)
        
        # 添加大量重複的熱門資源記錄
        duplicate_count = total_records - unique_count
        for i in range(duplicate_count):
            logs.append(hot_log)
        
        # 打亂順序
        random.shuffle(logs)
        return logs

    def generate_ttl_boundary_logs(self) -> Tuple[List[str], List[str]]:
        """生成TTL邊界測試日誌 (返回兩批相同的記錄)"""
        first_batch = []
        second_batch = []
        
        # 第一批記錄 (當前時間往前 1.5 小時，確保在處理窗口內)
        first_batch_base = self.base_timestamp - timedelta(hours=1, minutes=30)
        
        for i in range(100):
            timestamp1 = first_batch_base + timedelta(seconds=i*5)
            # 第二批設定為當前時間往前 10 分鐘 (模擬 TTL 過期後重新處理)
            timestamp2 = self.base_timestamp - timedelta(minutes=10) + timedelta(seconds=i*5)
            
            path = f"/prod/client/ttl-test/asset-boundary-{i:03d}.json"
            client_ip = self.client_ips[i % len(self.client_ips)]
            trace_id = self.generate_trace_id(f"ttl-boundary-{i:03d}")
            
            log1 = self.generate_log_entry(timestamp1, path, client_ip, trace_id)
            log2 = self.generate_log_entry(timestamp2, path, client_ip, trace_id)
            
            first_batch.append(log1)
            second_batch.append(log2)
        
        return first_batch, second_batch

def main():
    """生成所有測試日誌檔案"""
    generator = CDNLogGenerator()
    
    print("🚀 開始生成CDN日誌去重測試檔案...")
    print(f"⏰ 基準時間：{generator.base_timestamp.strftime('%Y-%m-%d %H:%M:%S')} (當前時間往前30分鐘)")
    print(f"📅 生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 處理窗口：{generator.base_timestamp.strftime('%H:%M:%S')} ~ {(generator.base_timestamp + timedelta(hours=2)).strftime('%H:%M:%S')}")
    
    # 1. 基礎去重測試
    print("📝 生成基礎去重測試日誌 (1000筆, 30%重複)...")
    basic_logs = generator.generate_basic_dedup_logs(1000, 0.3)
    with open('test_logs_basic_dedup_full.log', 'w') as f:
        f.write("# 基礎雙層去重測試日誌 - 1000筆記錄，30%重複率\n")
        f.write("# 預期結果 (雙層去重):\n")
        f.write("# - Redis 層：700個去重鍵存儲 (僅唯一記錄)\n")
        f.write("# - Publish：700次觸發，300次跳過\n")
        f.write("# - ClickHouse 寫入嘗試：1000次，最終記錄：700筆\n")
        f.write("# - 客戶端：700筆唯一記錄接收\n\n")
        for log in basic_logs:
            f.write(log + '\n')
    
    # 2. 並發去重測試 (5個處理器)
    print("🔄 生成並發去重測試日誌 (5個處理器, 50%跨處理器重複)...")
    for processor_id in range(1, 6):
        concurrent_logs = generator.generate_concurrent_dedup_logs(processor_id, 1000, 0.5)
        with open(f'test_logs_concurrent_processor{processor_id}_full.log', 'w') as f:
            f.write(f"# 並發去重測試 - 處理器{processor_id}日誌 (1000筆)\n")
            f.write("# 50%記錄與其他處理器重複\n\n")
            for log in concurrent_logs:
                f.write(log + '\n')
    
    # 3. 高頻重複測試
    print("⚡ 生成高頻重複測試日誌 (10000筆, 90%重複)...")
    high_freq_logs = generator.generate_high_frequency_dedup_logs(10000, 0.9)
    with open('test_logs_high_frequency_dedup_full.log', 'w') as f:
        f.write("# 高頻雙層去重測試日誌 - 10000筆記錄，90%重複率\n")
        f.write("# 預期結果 (雙層去重):\n")
        f.write("# - Redis 層：1000個去重鍵存儲\n")
        f.write("# - Publish：1000次觸發，9000次跳過\n")
        f.write("# - ClickHouse 寫入嘗試：10000次，最終記錄：1000筆\n")
        f.write("# - 客戶端：1000筆唯一記錄接收\n\n")
        for log in high_freq_logs:
            f.write(log + '\n')
    
    # 4. TTL邊界測試
    print("⏰ 生成TTL邊界測試日誌 (2小時邊界)...")
    first_batch, second_batch = generator.generate_ttl_boundary_logs()
    
    with open('test_logs_ttl_boundary_batch1.log', 'w') as f:
        f.write("# TTL雙層去重測試 - 第一批記錄 (當前時間往前1.5小時)\n")
        f.write("# Redis TTL=2小時，ClickHouse永久存儲\n")
        f.write("# 預期：Redis鍵設定，ClickHouse寫入成功，Publish觸發\n")
        f.write(f"# 生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for log in first_batch:
            f.write(log + '\n')
    
    with open('test_logs_ttl_boundary_batch2.log', 'w') as f:
        f.write("# TTL邊界測試 - 第二批記錄 (當前時間往前10分鐘)\n")
        f.write("# Redis TTL已過期，視為新記錄觸發Publish\n")
        f.write("# 但ClickHouse因內部去重拒絕寫入\n")
        f.write("# 關鍵驗證：客戶端收到重複記錄，ClickHouse無新增\n")
        f.write(f"# 生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for log in second_batch:
            f.write(log + '\n')
    
    print("✅ 所有測試日誌檔案生成完成！")
    print("\n📋 生成的檔案列表：")
    print("- test_logs_basic_dedup_full.log (基礎去重測試)")
    print("- test_logs_concurrent_processor[1-5]_full.log (並發去重測試)")
    print("- test_logs_high_frequency_dedup_full.log (高頻重複測試)")
    print("- test_logs_ttl_boundary_batch[1-2].log (TTL邊界測試)")

if __name__ == "__main__":
    main()
