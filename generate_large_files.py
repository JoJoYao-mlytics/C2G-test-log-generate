#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大檔案 CDN 日誌產生器 (支援分層目錄結構)
減少檔案數量，增加每個檔案的記錄數
支援分層目錄以避免單一目錄檔案過多
"""

import os
import sys
import glob
import gc
import psutil
from datetime import datetime
from generate_split_logs import generate_split_logs

def get_output_directory():
    """讓使用者輸入輸出目錄"""
    print("📁 設定輸出目錄")
    print("   預設目錄: /Users/jojo.yao/Downloads/Ali_test_log")
    
    while True:
        try:
            user_input = input("\n請輸入輸出目錄路徑 (直接按 Enter 使用預設): ").strip()
            
            if not user_input:
                # 使用預設目錄
                output_dir = "/Users/jojo.yao/Downloads/Ali_test_log"
            else:
                # 使用使用者輸入的目錄
                output_dir = os.path.expanduser(user_input)
            
            # 檢查目錄是否存在，不存在則詢問是否建立
            if not os.path.exists(output_dir):
                create = input(f"目錄 '{output_dir}' 不存在，是否建立? (Y/n): ").strip().lower()
                if create in ['', 'y', 'yes']:
                    try:
                        os.makedirs(output_dir, exist_ok=True)
                        print(f"✅ 成功建立目錄: {output_dir}")
                    except Exception as e:
                        print(f"❌ 無法建立目錄: {e}")
                        continue
                else:
                    print("❌ 請選擇其他目錄")
                    continue
            
            # 檢查目錄是否可寫
            if not os.access(output_dir, os.W_OK):
                print(f"❌ 目錄 '{output_dir}' 沒有寫入權限")
                continue
            
            # 檢查是否有現有檔案
            existing_files = glob.glob(os.path.join(output_dir, "qatest_*.log.gz"))
            if existing_files:
                print(f"⚠️  發現 {len(existing_files)} 個現有的測試檔案")
                overwrite = input("是否要清理現有檔案? (y/N): ").strip().lower()
                if overwrite in ['y', 'yes']:
                    for file in existing_files:
                        try:
                            os.remove(file)
                        except Exception as e:
                            print(f"❌ 無法刪除檔案 {file}: {e}")
                    print("✅ 已清理現有檔案")
            
            return output_dir
            
        except KeyboardInterrupt:
            print("\n👋 已取消")
            sys.exit(0)
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            continue

def check_system_resources():
    """檢查系統資源"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    print(f"💻 系統資源檢查:")
    print(f"   - 可用記憶體: {memory.available / 1024 / 1024 / 1024:.1f} GB")
    print(f"   - 記憶體使用率: {memory.percent:.1f}%")
    print(f"   - 可用磁碟空間: {disk.free / 1024 / 1024 / 1024:.1f} GB")
    
    # 記憶體警告
    if memory.percent > 80:
        print("⚠️  警告: 記憶體使用率過高，建議選擇較小的方案")
        return False
    
    # 磁碟空間警告
    if disk.free < 5 * 1024 * 1024 * 1024:  # 小於 5GB
        print("⚠️  警告: 磁碟空間不足 5GB，可能無法完成大型任務")
        return False
    
    return True

def generate_large_files():
    """產生較少但較大的檔案"""
    
    print("🚀 產生大檔案CDN日誌...")
    print("📋 方案說明: 減少檔案數量，增加每個檔案的記錄數")
    
    # 檢查系統資源
    if not check_system_resources():
        proceed = input("\n系統資源可能不足，是否繼續? (y/N): ").strip().lower()
        if proceed not in ['y', 'yes']:
            print("👋 已取消")
            return
    
    # 讓使用者選擇輸出目錄
    output_dir = get_output_directory()
    
    # 不同的方案
    options = {
        '1': {
            'name': '3500個檔案，每檔10000筆 (分層目錄)',
            'files': 3500,
            'records_per_file': 10000,
            'total_records': 35000000,
            'description': '達到3500萬筆記錄，3500個.gz檔案，分層目錄結構',
            'use_hierarchy': True,
            'files_per_dir': 1000
        },
        '2': {
            'name': '1000個檔案，每檔35000筆 (分層目錄)',
            'files': 1000,
            'records_per_file': 35000,
            'total_records': 35000000,
            'description': '達到3500萬筆記錄，1000個.gz檔案，分層目錄結構',
            'use_hierarchy': True,
            'files_per_dir': 500
        },
        '3': {
            'name': '350個檔案，每檔100000筆 (單層目錄)',
            'files': 350,
            'records_per_file': 100000,
            'total_records': 35000000,
            'description': '達到3500萬筆記錄，350個.gz檔案，單層目錄',
            'use_hierarchy': False,
            'files_per_dir': 0
        },
        '4': {
            'name': '10個檔案，每檔100筆 (測試)',
            'files': 10,
            'records_per_file': 100,
            'total_records': 1000,
            'description': '小型測試：1000筆記錄，10個.gz檔案',
            'use_hierarchy': False,
            'files_per_dir': 0
        }
    }
    
    print("\n📋 請選擇方案:")
    for key, option in options.items():
        print(f"   {key}. {option['description']}")
    
    while True:
        try:
            choice = input("\n請選擇 (1-4): ").strip()
            if choice in options:
                break
            else:
                print("❌ 無效選擇，請輸入 1-4")
        except KeyboardInterrupt:
            print("\n👋 已取消")
            sys.exit(0)
    
    selected = options[choice]
    
    print(f"\n📊 選擇的方案: {selected['name']}")
    print(f"   - 檔案數量: {selected['files']:,} 個")
    print(f"   - 每檔記錄數: {selected['records_per_file']:,} 筆")
    print(f"   - 總記錄數: {selected['total_records']:,} 筆")
    print(f"   - 檔案格式: .log.gz (gzip 壓縮)")
    print(f"   - 目錄結構: {'分層目錄' if selected['use_hierarchy'] else '單層目錄'}")
    if selected['use_hierarchy']:
        total_dirs = (selected['files'] + selected['files_per_dir'] - 1) // selected['files_per_dir']
        print(f"   - 每目錄檔案數: {selected['files_per_dir']:,} 個")
        print(f"   - 總目錄數: {total_dirs:,} 個")
    print(f"   - 預估單檔大小: ~{selected['records_per_file'] * 0.5 / 1024:.1f} MB")
    print(f"   - 預估總大小: ~{selected['total_records'] * 0.5 / 1024 / 1024:.1f} GB")
    
    # 確認執行
    confirm = input(f"\n確定要執行嗎? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("👋 已取消")
        sys.exit(0)
    
    print("=" * 60)
    
    # 產生現在時間的字串
    now = datetime.now()
    current_time_str = now.strftime('%d/%b/%Y:%H:%M:%S +0000')
    
    print(f"⏰ 使用當前時間: {current_time_str}")
    
    # 使用使用者選擇的目錄
    base_dir = output_dir
    
    try:
        if selected['use_hierarchy']:
            # 使用分層目錄結構
            print(f"📂 使用分層目錄結構...")
            generate_hierarchical_structure(selected, base_dir, current_time_str)
        else:
            # 使用單層目錄結構
            print(f"📁 使用單層目錄結構...")
            generate_single_directory(selected, base_dir, current_time_str)
        
        print(f"\n🎉 任務完成!")
        print(f"📁 檔案位置: {base_dir}")
        print(f"✅ 所有檔案均為 .log.gz 格式")
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

def generate_hierarchical_structure(selected, base_dir, current_time_str):
    """使用分層目錄結構產生檔案 - 記憶體優化版本"""
    
    total_files = selected['files']
    files_per_dir = selected['files_per_dir']
    records_per_file = selected['records_per_file']
    
    # 計算需要的目錄數
    total_dirs = (total_files + files_per_dir - 1) // files_per_dir
    
    print(f"📁 目錄結構規劃:")
    print(f"   - 總檔案數: {total_files:,}")
    print(f"   - 每目錄檔案數: {files_per_dir:,}")
    print(f"   - 總目錄數: {total_dirs:,}")
    print(f"   - 基礎目錄: {base_dir}")
    
    # 建立基礎目錄
    os.makedirs(base_dir, exist_ok=True)
    
    total_generated = 0
    
    for i in range(total_dirs):
        # 記憶體檢查
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            print(f"⚠️  記憶體使用率達到 {memory.percent:.1f}%，執行垃圾回收...")
            gc.collect()
            memory = psutil.virtual_memory()
            print(f"   回收後記憶體使用率: {memory.percent:.1f}%")
            
            if memory.percent > 90:
                print("❌ 記憶體不足，建議重啟程式或選擇較小的方案")
                raise MemoryError("記憶體不足")
        
        # 計算這個目錄的檔案範圍
        start_file = i * files_per_dir + 1
        end_file = min((i + 1) * files_per_dir, total_files)
        current_dir_files = end_file - start_file + 1
        
        # 建立子目錄
        dir_name = f"batch_{i+1:03d}"
        dir_path = os.path.join(base_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        
        print(f"\n📂 處理目錄 {i+1:3d}/{total_dirs}: {dir_name}")
        print(f"   檔案範圍: {start_file:06d} ~ {end_file:06d}")
        print(f"   檔案數量: {current_dir_files:,}")
        print(f"   記憶體使用: {memory.percent:.1f}%")
        
        # 計算這個目錄的記錄數
        records_count = current_dir_files * records_per_file
        
        # 記憶體優化的配置
        config = {
            'total_count': records_count,
            'records_per_file': records_per_file,
            'start_time_str': current_time_str,
            'interval': 0.001,  # 加快產生速度
            'output_dir': dir_path,
            'file_prefix': 'qatest_',
            'verbose': False,  # 關閉詳細輸出以提高速度
            'memory_optimized': True  # 啟用記憶體優化模式
        }
        
        try:
            # 產生分割日誌
            generate_split_logs(**config)
            
            # 重新命名檔案以符合全域編號
            rename_files_in_directory(dir_path, start_file)
            
            total_generated += records_count
            progress = (total_generated / selected['total_records']) * 100
            
            print(f"   ✅ 完成! 已產生 {total_generated:,} / {selected['total_records']:,} 筆記錄 ({progress:.1f}%)")
            
            # 每完成一個目錄就執行垃圾回收
            if i % 10 == 0:  # 每10個目錄執行一次
                gc.collect()
                
        except Exception as e:
            print(f"   ❌ 處理目錄 {dir_name} 時發生錯誤: {e}")
            raise

def generate_single_directory(selected, base_dir, current_time_str):
    """使用單層目錄結構產生檔案 - 記憶體優化版本"""
    
    print(f"📁 單層目錄結構:")
    print(f"   - 總檔案數: {selected['files']:,}")
    print(f"   - 每檔記錄數: {selected['records_per_file']:,}")
    print(f"   - 輸出目錄: {base_dir}")
    
    # 建立輸出目錄
    os.makedirs(base_dir, exist_ok=True)
    
    # 記憶體檢查
    memory = psutil.virtual_memory()
    print(f"   - 記憶體使用: {memory.percent:.1f}%")
    
    if memory.percent > 80:
        print("⚠️  記憶體使用率較高，建議使用分層目錄結構")
        proceed = input("是否繼續? (y/N): ").strip().lower()
        if proceed not in ['y', 'yes']:
            return
    
    # 記憶體優化的執行配置
    config = {
        'total_count': selected['total_records'],
        'records_per_file': selected['records_per_file'],
        'start_time_str': current_time_str,
        'interval': 0.001,  # 更快的間隔
        'output_dir': base_dir,
        'file_prefix': 'qatest_',
        'verbose': True,
        'memory_optimized': True  # 啟用記憶體優化模式
    }
    
    try:
        generate_split_logs(**config)
        
        # 執行最終垃圾回收
        gc.collect()
        final_memory = psutil.virtual_memory()
        print(f"📊 完成後記憶體使用率: {final_memory.percent:.1f}%")
        
    except Exception as e:
        print(f"❌ 產生檔案時發生錯誤: {e}")
        raise

def rename_files_in_directory(dir_path, start_file_number):
    """重新命名目錄中的檔案以符合全域編號"""
    
    # 找到目錄中的所有 .gz 檔案
    pattern = os.path.join(dir_path, "qatest_*.log.gz")
    files = glob.glob(pattern)
    files.sort()
    
    # 重新命名檔案
    for i, old_filepath in enumerate(files):
        global_file_number = start_file_number + i
        new_filename = f"qatest_{global_file_number:06d}.log.gz"
        new_filepath = os.path.join(dir_path, new_filename)
        
        if old_filepath != new_filepath:
            os.rename(old_filepath, new_filepath)

def main():
    generate_large_files()

if __name__ == "__main__":
    main()

