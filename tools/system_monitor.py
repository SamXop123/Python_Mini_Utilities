"""
System Resource Monitor - Display real-time system statistics including CPU, memory, disk usage, and running processes.
Works on Windows, macOS, and Linux.
"""

import os
import sys
import time
import platform
from collections import namedtuple

# Try to import psutil, use fallback methods if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️  Warning: psutil not found. Using limited monitoring capabilities.")

ProcessInfo = namedtuple('ProcessInfo', ['name', 'cpu_percent', 'memory_mb', 'pid'])

class SystemMonitor:
    def __init__(self):
        self.system = platform.system()
        self.boot_time = None
        
    def get_cpu_info(self):
        """Get CPU usage and information"""
        if HAS_PSUTIL:
            try:
                # Get CPU usage with a small interval for better accuracy
                psutil.cpu_percent(interval=0.1, percpu=True) 
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Get physical and logical core counts
                logical_cores = psutil.cpu_count()
                physical_cores = psutil.cpu_count(logical=False) or logical_cores
                
                # Get CPU frequency
                try:
                    if self.system == "Windows":
                        import wmi
                        w = wmi.WMI()
                        cpu_info = w.Win32_Processor()[0]
                        current_freq = cpu_info.CurrentClockSpeed
                        max_freq = cpu_info.MaxClockSpeed
                        freq_str = f"{current_freq:.0f} MHz (Max: {max_freq} MHz)"
                    else:
                        cpu_freq = psutil.cpu_freq()
                        freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "Unknown"
                except:
                    freq_str = "Unknown"
                
                info = {
                    'usage': cpu_percent,
                    'logical_cores': logical_cores,
                    'physical_cores': physical_cores,
                    'frequency': freq_str
                }
                
                # get temperature
                try:
                    if self.system == "Windows":
                        temps = psutil.sensors_temperatures()
                        if temps:
                            temp = list(temps.values())[0][0].current
                            info['temperature'] = f"{temp:.0f}°C"
                except:
                    pass
                
                return info
            except:
                pass
        
        # Fallback handling
        return {
            'usage': "Unknown",
            'cores': os.cpu_count(),
            'frequency': "Unknown"
        }
    

    # Get memory usage information
    def get_memory_info(self):
        if HAS_PSUTIL:
            try:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                return {
                    'total': self.format_bytes(memory.total),
                    'available': self.format_bytes(memory.available),
                    'used': self.format_bytes(memory.used),
                    'percent': memory.percent,
                    'swap_total': self.format_bytes(swap.total),
                    'swap_used': self.format_bytes(swap.used),
                    'swap_percent': swap.percent
                }
            except:
                pass
        
        # Fallback
        return {
            'total': "Unknown",
            'available': "Unknown", 
            'used': "Unknown",
            'percent': "Unknown",
            'swap_total': "Unknown",
            'swap_used': "Unknown",
            'swap_percent': "Unknown"
        }
    

    # Get disk usage information
    def get_disk_info(self):
        disk_info = []
        
        if HAS_PSUTIL:
            try:
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info.append({
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'total': self.format_bytes(usage.total),
                            'used': self.format_bytes(usage.used),
                            'free': self.format_bytes(usage.free),
                            'percent': (usage.used / usage.total) * 100
                        })
                    except:
                        continue
            except:
                pass
        
        # Fallback
        if not disk_info:
            try:
                current = os.path.abspath('.')
                if self.system == "Windows":
                    import shutil
                    total, used, free = shutil.disk_usage(current)
                    disk_info.append({
                        'device': "C:",
                        'mountpoint': current,
                        'total': self.format_bytes(total),
                        'used': self.format_bytes(used),
                        'free': self.format_bytes(free),
                        'percent': (used / total) * 100
                    })
            except:
                pass
        
        return disk_info
    
    # Get top resource-consuming processes
    def get_top_processes(self, limit=10):
        processes = []
        
        if not HAS_PSUTIL:
            return processes
            
        try:
            # First pass to get CPU times
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    # Initialize CPU percent calculation
                    proc.cpu_percent(interval=0.0)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Small delay to get CPU usage
            time.sleep(0.5)
            
            # Second pass to get actual CPU usage
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    with proc.oneshot():
                        # Get process name
                        name = proc.info['name']
                        if name.endswith('.exe'):
                            name = name[:-4]
                        
                        # Get memory usage
                        memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                        
                        # Get CPU percent (already calculated from first pass)
                        cpu_percent = proc.info['cpu_percent'] / psutil.cpu_count()
                        
                        # Skip system processes
                        if name.lower() in ['system', 'system idle process', 'system interrupts']:
                            continue
                        
                        processes.append(ProcessInfo(
                            name=name,
                            cpu_percent=round(cpu_percent, 1),
                            memory_mb=round(memory_mb, 1),
                            pid=proc.info['pid']
                        ))
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage and return top processes
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            return processes[:limit]
            
        except Exception as e:
            print(f"\n⚠️  Error getting process info: {str(e)}")
            return []
    

    # Format bytes in human readable format
    def format_bytes(self, bytes_value):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} PB"
    

    # Get basic system information
    def get_system_info(self):
        return {
            'platform': platform.platform(),
            'system': self.system,
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0]
        }
    

    # Display system information header
    def display_header(self):
        info = self.get_system_info()
        print("\n" + "="*60)
        print("🖥️  SYSTEM RESOURCE MONITOR")
        print("="*60)
        print(f"💻 Platform: {info['platform']}")
        print(f"🐍 Python: {info['python_version']}")
        print(f"🏗️  Architecture: {info['architecture']}")
        print("="*60)
    

    # Display CPU information
    def display_cpu_info(self, cpu_info):
        print(f"\n💻 CPU Usage: {cpu_info['usage']}% "
              f"({cpu_info['physical_cores']} physical, {cpu_info['logical_cores']} logical cores)")
        if 'temperature' in cpu_info:
            print(f"🌡️  Temperature: {cpu_info['temperature']}")
        print(f"⚡ Frequency: {cpu_info['frequency']}")
    

    # Display memory information
    def display_memory_info(self, memory_info):
        print(f"\n🧠 Memory: {memory_info['used']} / {memory_info['total']} ({memory_info['percent']}%)")
        print(f"💾 Available: {memory_info['available']}")
        if memory_info['swap_total'] != "0 B":
            print(f"🔄 Swap: {memory_info['swap_used']} / {memory_info['swap_total']} ({memory_info['swap_percent']}%)")
    

    # Display disk information
    def display_disk_info(self, disk_info):
        print(f"\n💾 Disk Usage:")
        for disk in disk_info:
            print(f"   {disk['device']} ({disk['mountpoint']})")
            print(f"   {disk['used']} / {disk['total']} ({disk['percent']:.1f}%)")
    

    # Display processes
    def display_processes(self, processes):

        # Sort by CPU usage (descending)
        processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        
        # Take top N processes
        top_processes = processes[:10]  # Show top 10 instead of 5
        
        if not top_processes:
            print("\nNo active processes found!")
            return
            
        print(f"\n{'':<4}{'Process':<25}{'CPU %':>8}{'Memory (MB)':>12}{'PID':>10}")
        print("-" * 60)
        
        for i, proc in enumerate(top_processes, 1):
            # Truncate long process names
            name = proc.name if len(proc.name) <= 22 else proc.name[:19] + '...'
            print(f"{i:2d}. {name:<25}{proc.cpu_percent:>7.1f}%{proc.memory_mb:>10.1f}{proc.pid:>10}")
        
        # Show total resource usage
        total_cpu = sum(p.cpu_percent for p in processes)
        total_mem = sum(p.memory_mb for p in processes)
        print("-" * 60)
        print(f"{'Total:':>29}{total_cpu:>7.1f}%{total_mem:>10.1f} MB")
    

    # Display system resources once
    def monitor_once(self):

        self.display_header()
        
        cpu_info = self.get_cpu_info()
        self.display_cpu_info(cpu_info)
        
        memory_info = self.get_memory_info()
        self.display_memory_info(memory_info)
        
        disk_info = self.get_disk_info()
        self.display_disk_info(disk_info)
        
        # Get and display processes
        processes = self.get_top_processes(limit=10)  # Get top 10 processes
        self.display_processes(processes)
        
        print("="*60)
    

    # Continuously monitor system resources
    def monitor_continuous(self, interval=2):
        try:
            while True:
                os.system('cls' if self.system == 'Windows' else 'clear')
                self.monitor_once()
                print(f"\n⏱️  Refreshing every {interval} seconds... Press Ctrl+C to stop")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped. Goodbye!")


def main():
    monitor = SystemMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = 2
        if len(sys.argv) > 2:
            try:
                interval = int(sys.argv[2])
            except ValueError:
                print("⚠️  Invalid interval. Using default of 2 seconds.")
        
        monitor.monitor_continuous(interval)
    else:
        monitor.monitor_once()
        
        print("\n💡 For continuous monitoring, run:")
        print("   python system_monitor.py --continuous [interval_seconds]")


if __name__ == "__main__":
    main()
