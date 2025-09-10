#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分割式 CDN 日誌產生器
產生35萬筆日誌，每100筆切一個檔案，使用 gzip 壓縮
檔案名稱格式: qatest_NNNN.gz
"""

import gzip
import os
import datetime
from cdn_log_generator import CDNLogGenerator
import argparse
import sys

def generate_split_logs(total_count: int = 350000,
                       records_per_file: int = 100,
                       start_time_str: str = "21/Aug/2025:15:05:11 +0000",
                       interval: float = 0.1,
                       output_dir: str = "/Users/jojo.yao/Project/BMad/qa_doc/Ali",
                       file_prefix: str = "qatest_",
                       verbose: bool = True):
    """
    產生分割的壓縮日誌檔案
    
    Args:
        total_count: 總記錄數量
        records_per_file: 每個檔案的記錄數量
        start_time_str: 開始時間字串
        interval: 時間間隔（秒）
        output_dir: 輸出目錄
        file_prefix: 檔案名稱前綴
        verbose: 是否顯示詳細資訊
    """
    
    # 解析開始時間
    try:
        start_time = datetime.datetime.strptime(start_time_str, '%d/%b/%Y:%H:%M:%S +0000')
    except ValueError:
        print(f"錯誤: 無法解析時間格式 '{start_time_str}'", file=sys.stderr)
        print("正確格式: DD/MMM/YYYY:HH:MM:SS +0000", file=sys.stderr)
        sys.exit(1)
    
    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 計算需要的檔案數量
    total_files = (total_count + records_per_file - 1) // records_per_file
    
    if verbose:
        print(f"開始產生分割日誌檔案...")
        print(f"總記錄數: {total_count:,}")
        print(f"每檔記錄數: {records_per_file}")
        print(f"總檔案數: {total_files}")
        print(f"開始時間: {start_time_str}")
        print(f"時間間隔: {interval} 秒")
        print(f"輸出目錄: {output_dir}")
        print(f"檔案前綴: {file_prefix}")
        print("-" * 50)
    
    # 建立產生器
    generator = CDNLogGenerator()
    current_time = start_time
    total_generated = 0
    
    # 產生每個檔案
    for file_index in range(total_files):
        # 計算這個檔案要產生的記錄數
        remaining_records = total_count - total_generated
        current_file_records = min(records_per_file, remaining_records)
        
        if current_file_records <= 0:
            break
        
        # 產生檔案名稱 (6位數字，補零) - 解壓縮後為 .log 檔案
        filename = f"{file_prefix}{file_index + 1:06d}.log.gz"
        filepath = os.path.join(output_dir, filename)
        
        if verbose:
            print(f"正在產生檔案 {file_index + 1:6d}/{total_files}: {filename} ({current_file_records} 筆記錄)")
        
        # 產生這個檔案的日誌記錄
        logs = generator.generate_logs(current_time, current_file_records, interval)
        
        # 寫入壓縮檔案
        try:
            with gzip.open(filepath, 'wt', encoding='utf-8') as gz_file:
                for log in logs:
                    gz_file.write(log + '\n')
            
            if verbose:
                file_size = os.path.getsize(filepath)
                print(f"    完成: {filename} ({file_size:,} bytes)")
        
        except Exception as e:
            print(f"錯誤: 無法寫入檔案 {filename}: {e}", file=sys.stderr)
            continue
        
        # 更新計數器和時間
        total_generated += current_file_records
        current_time += datetime.timedelta(seconds=interval * current_file_records)
        
        # 顯示進度
        if verbose and (file_index + 1) % 1000 == 0:
            progress = (total_generated / total_count) * 100
            print(f"    進度: {total_generated:,}/{total_count:,} ({progress:.1f}%)")
    
    if verbose:
        print("-" * 50)
        print(f"完成!")
        print(f"總計產生: {total_generated:,} 筆記錄")
        print(f"檔案數量: {file_index + 1}")
        print(f"唯一性統計:")
        print(f"  - 客戶端 ID: {len(generator.used_client_ids):,}")
        print(f"  - 追蹤 ID: {len(generator.used_trace_ids):,}")
        print(f"  - 組合鍵: {len(generator.used_combinations):,}")
        
        # 計算總檔案大小
        total_size = 0
        for i in range(file_index + 1):
            filename = f"{file_prefix}{i + 1:06d}.log.gz"
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
        
        print(f"總檔案大小: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")

def verify_generated_files(output_dir: str = "/Users/jojo.yao/Project/BMad/qa_doc/Ali",
                          file_prefix: str = "qatest_",
                          expected_files: int = 3500):
    """
    驗證產生的檔案
    
    Args:
        output_dir: 輸出目錄
        file_prefix: 檔案前綴
        expected_files: 預期檔案數量
    """
    print("\n驗證產生的檔案...")
    
    found_files = []
    total_records = 0
    total_size = 0
    
    for i in range(1, expected_files + 1):
        filename = f"{file_prefix}{i:06d}.log.gz"
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            found_files.append(filename)
            file_size = os.path.getsize(filepath)
            total_size += file_size
            
            # 讀取檔案計算記錄數
            try:
                with gzip.open(filepath, 'rt', encoding='utf-8') as gz_file:
                    record_count = sum(1 for line in gz_file if line.strip())
                    total_records += record_count
            except Exception as e:
                print(f"警告: 無法讀取檔案 {filename}: {e}")
    
    print(f"找到檔案: {len(found_files)}/{expected_files}")
    print(f"總記錄數: {total_records:,}")
    print(f"總檔案大小: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    
    if len(found_files) == expected_files:
        print("✅ 所有檔案都已成功產生!")
    else:
        print(f"⚠️  缺少 {expected_files - len(found_files)} 個檔案")
    
    # 顯示前幾個和後幾個檔案
    if found_files:
        print(f"\n前5個檔案: {found_files[:5]}")
        print(f"後5個檔案: {found_files[-5:]}")

def main():
    parser = argparse.ArgumentParser(description='分割式 CDN 日誌產生器')
    parser.add_argument('--total-count', '-t', type=int, default=350000,
                       help='總記錄數量 (預設: 350000)')
    parser.add_argument('--records-per-file', '-r', type=int, default=100,
                       help='每個檔案的記錄數量 (預設: 100)')
    parser.add_argument('--start-time', '-s', type=str, 
                       default='21/Aug/2025:15:05:11 +0000',
                       help='開始時間 (格式: DD/MMM/YYYY:HH:MM:SS +0000)')
    parser.add_argument('--interval', '-i', type=float, default=0.1,
                       help='時間間隔秒數 (預設: 0.1)')
    parser.add_argument('--output-dir', '-o', type=str,
                       default='/Users/jojo.yao/Project/BMad/qa_doc/Ali',
                       help='輸出目錄')
    parser.add_argument('--prefix', '-p', type=str, default='qatest_',
                       help='檔案名稱前綴 (預設: qatest_)')
    parser.add_argument('--verify', action='store_true',
                       help='產生完成後驗證檔案')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='靜默模式，不顯示詳細資訊')
    
    args = parser.parse_args()
    
    # 產生分割日誌
    generate_split_logs(
        total_count=args.total_count,
        records_per_file=args.records_per_file,
        start_time_str=args.start_time,
        interval=args.interval,
        output_dir=args.output_dir,
        file_prefix=args.prefix,
        verbose=not args.quiet
    )
    
    # 驗證檔案（如果要求）
    if args.verify:
        expected_files = (args.total_count + args.records_per_file - 1) // args.records_per_file
        verify_generated_files(
            output_dir=args.output_dir,
            file_prefix=args.prefix,
            expected_files=expected_files
        )

if __name__ == "__main__":
    main()
