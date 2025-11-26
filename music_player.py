import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yt_dlp
import pygame
import os
import threading
import requests
import time
import sys
import subprocess
from lyric_fetcher import LyricFetcher

# 尝试导入static_ffmpeg，如果失败则使用系统ffmpeg
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

class BilibiliMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("B站音乐播放器 v1.0")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e1e')
        
        # 初始化组件
        pygame.mixer.init()
        self.lyric_fetcher = LyricFetcher()
        
        # 当前状态
        self.current_song = None
        self.is_playing = False
        self.playlist = []
        self.current_index = 0
        self.song_duration = 0
        
        # 检查ffmpeg
        self.check_ffmpeg()
        
        self.setup_ui()
        
    def check_ffmpeg(self):
        """检查ffmpeg是否可用"""
        try:
            # 尝试运行ffmpeg命令
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe文件
                base_path = sys._MEIPASS
                ffmpeg_path = os.path.join(base_path, 'static_ffmpeg', 'bin', 'ffmpeg.exe')
                if os.path.exists(ffmpeg_path):
                    self.ffmpeg_location = os.path.join(base_path, 'static_ffmpeg', 'bin')
                else:
                    self.ffmpeg_location = None
            else:
                # 如果是Python脚本
                result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.ffmpeg_location = None  # 使用系统ffmpeg
                else:
                    # 尝试使用static_ffmpeg
                    try:
                        import static_ffmpeg
                        static_ffmpeg.add_paths()
                        self.ffmpeg_location = 'static_ffmpeg'
                    except:
                        self.ffmpeg_location = None
        except:
            self.ffmpeg_location = None
            
    def get_ydl_opts(self):
        """获取yt-dlp配置"""
        base_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        # 如果有ffmpeg路径，添加到配置中
        if self.ffmpeg_location:
            base_opts['ffmpeg_location'] = self.ffmpeg_location
            
        return base_opts
        
    def setup_ui(self):
        # 主框架
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 标题区域
        title_frame = tk.Frame(main_frame, bg='#1e1e1e')
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="🎵 B站音乐播放器", 
                              font=('Arial', 18, 'bold'), 
                              fg='#4CAF50', bg='#1e1e1e')
        title_label.pack(side=tk.LEFT)
        
        # 显示ffmpeg状态
        ffmpeg_status = "✅ FFmpeg可用" if self.ffmpeg_location or self.check_ffmpeg_system() else "⚠️ FFmpeg未找到，音频转换可能失败"
        status_label = tk.Label(title_frame, text=ffmpeg_status, 
                               fg='yellow' if not (self.ffmpeg_location or self.check_ffmpeg_system()) else 'green',
                               bg='#1e1e1e', font=('Arial', 9))
        status_label.pack(side=tk.RIGHT)
        
        # 下载区域
        download_frame = tk.LabelFrame(main_frame, text=" 下载音乐 ", 
                                      font=('Arial', 10, 'bold'),
                                      fg='white', bg='#1e1e1e', bd=1)
        download_frame.pack(fill=tk.X, pady=(0, 15))
        
        # URL输入
        url_frame = tk.Frame(download_frame, bg='#1e1e1e')
        url_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(url_frame, text="B站视频链接:", 
                fg='white', bg='#1e1e1e', font=('Arial', 10)).pack(side=tk.LEFT)
        
        self.url_entry = tk.Entry(url_frame, width=70, bg='#333', fg='white', 
                                 insertbackground='white', font=('Arial', 10))
        self.url_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.url_entry.insert(0, "https://www.bilibili.com/video/...")
        
        # 按钮框架
        btn_frame = tk.Frame(download_frame, bg='#1e1e1e')
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Button(btn_frame, text="📥 下载单个音乐", command=self.download_music,
                 bg='#4CAF50', fg='white', font=('Arial', 10), width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📚 批量下载合集", command=self.batch_download,
                 bg='#2196F3', fg='white', font=('Arial', 10), width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔄 刷新列表", command=self.refresh_playlist,
                 bg='#FF9800', fg='white', font=('Arial', 10), width=12).pack(side=tk.LEFT, padx=5)
        
        # 进度显示
        self.progress = ttk.Progressbar(download_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = tk.Label(download_frame, text="👆 请输入B站视频链接并点击下载", 
                                    fg='#BB86FC', bg='#1e1e1e', font=('Arial', 9))
        self.status_label.pack(pady=(0, 10))
        
        # 播放控制区域
        control_frame = tk.LabelFrame(main_frame, text=" 播放控制 ", 
                                     font=('Arial', 10, 'bold'),
                                     fg='white', bg='#1e1e1e', bd=1)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        control_btn_frame = tk.Frame(control_frame, bg='#1e1e1e')
        control_btn_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.play_btn = tk.Button(control_btn_frame, text="▶️ 播放", 
                                 command=self.toggle_play, 
                                 bg='#FF5722', fg='white', font=('Arial', 11), width=8)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_btn_frame, text="⏮️ 上一首", 
                 command=self.previous_song, 
                 bg='#607D8B', fg='white', font=('Arial', 10), width=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_btn_frame, text="⏭️ 下一首", 
                 command=self.next_song, 
                 bg='#607D8B', fg='white', font=('Arial', 10), width=8).pack(side=tk.LEFT, padx=5)
        
        # 播放信息
        info_frame = tk.Frame(control_frame, bg='#1e1e1e')
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.current_song_label = tk.Label(info_frame, text="当前未播放", 
                                          fg='#4CAF50', bg='#1e1e1e', font=('Arial', 10, 'bold'))
        self.current_song_label.pack(side=tk.LEFT)
        
        self.time_label = tk.Label(info_frame, text="00:00 / 00:00", 
                                  fg='white', bg='#1e1e1e', font=('Arial', 9))
        self.time_label.pack(side=tk.RIGHT)
        
        # 播放进度条
        self.song_progress = ttk.Scale(control_frame, from_=0, to=100, 
                                      orient=tk.HORIZONTAL, command=self.seek_music)
        self.song_progress.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 音量控制
        volume_frame = tk.Frame(control_frame, bg='#1e1e1e')
        volume_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(volume_frame, text="🔊 音量:", fg='white', bg='#1e1e1e').pack(side=tk.LEFT)
        self.volume_scale = tk.Scale(volume_frame, from_=0, to=100, 
                                    orient=tk.HORIZONTAL, command=self.set_volume,
                                    bg='#333', fg='white', highlightbackground='#1e1e1e',
                                    length=150)
        self.volume_scale.set(70)
        self.volume_scale.pack(side=tk.LEFT, padx=5)
        
        # 内容区域（歌词和播放列表）
        content_frame = tk.Frame(main_frame, bg='#1e1e1e')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 歌词区域
        lyric_frame = tk.LabelFrame(content_frame, text=" 📝 歌词 ", 
                                   font=('Arial', 10, 'bold'),
                                   fg='white', bg='#1e1e1e', bd=1)
        lyric_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.lyric_text = scrolledtext.ScrolledText(lyric_frame, height=15, 
                                                   bg='#2d2d2d', fg='white',
                                                   font=('Arial', 11), wrap=tk.WORD)
        self.lyric_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.lyric_text.insert(tk.END, "🎵 歌词将在这里显示...\n\n下载音乐后会自动获取歌词")
        
        # 播放列表区域
        playlist_frame = tk.LabelFrame(content_frame, text=" 🎶 播放列表 ", 
                                      font=('Arial', 10, 'bold'),
                                      fg='white', bg='#1e1e1e', bd=1)
        playlist_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        playlist_frame.config(width=300)
        
        # 播放列表控制
        playlist_control_frame = tk.Frame(playlist_frame, bg='#1e1e1e')
        playlist_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(playlist_control_frame, text="🗑️ 删除", 
                 command=self.remove_song, bg='#f44336', fg='white',
                 font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(playlist_control_frame, text="🧹 清空", 
                 command=self.clear_playlist, bg='#ff9800', fg='white',
                 font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        
        # 播放列表
        self.playlist_box = tk.Listbox(playlist_frame, bg='#2d2d2d', fg='white',
                                      selectbackground='#4CAF50', font=('Arial', 10))
        self.playlist_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.playlist_box.bind('<<ListboxSelect>>', self.on_playlist_select)
        self.playlist_box.bind('<Double-Button-1>', self.on_double_click)
        
        # 初始化
        self.set_volume(70)
        self.scan_downloads_folder()
        self.update_progress()
        
    def check_ffmpeg_system(self):
        """检查系统ffmpeg是否可用"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
        
    def scan_downloads_folder(self):
        """扫描下载文件夹中的音乐文件"""
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
            return
            
        for file in os.listdir("downloads"):
            if file.endswith('.mp3'):
                file_path = os.path.join("downloads", file)
                song_info = {
                    'title': file.replace('.mp3', ''),
                    'file': file_path,
                    'duration': 0
                }
                if song_info not in self.playlist:
                    self.playlist.append(song_info)
                    
        self.update_playlist()
        
    def download_music(self):
        url = self.url_entry.get().strip()
        if not url or "bilibili.com" not in url:
            messagebox.showerror("错误", "请输入有效的B站视频链接")
            return
            
        threading.Thread(target=self._download_music, args=(url,), daemon=True).start()
        
    def _download_music(self, url):
        try:
            self.progress.start()
            self.status_label.config(text="⏳ 正在获取视频信息...")
            
            if not os.path.exists("downloads"):
                os.makedirs("downloads")
                
            ydl_opts = self.get_ydl_opts()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                mp3_file = filename.rsplit('.', 1)[0] + '.mp3'
                
                song_info = {
                    'title': info.get('title', '未知标题'),
                    'file': mp3_file,
                    'duration': info.get('duration', 0)
                }
                
                self.playlist.append(song_info)
                self.root.after(0, self.update_playlist)
                
                self.status_label.config(text=f"✅ 下载完成: {song_info['title']}")
                
        except Exception as e:
            error_msg = f"❌ 下载失败: {str(e)}"
            self.status_label.config(text=error_msg)
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            self.progress.stop()
            
    def batch_download(self):
        url = self.url_entry.get().strip()
        if not url or "bilibili.com" not in url:
            messagebox.showerror("错误", "请输入有效的B站合集链接")
            return
            
        threading.Thread(target=self._batch_download, args=(url,), daemon=True).start()
        
    def _batch_download(self, url):
        try:
            self.progress.start()
            self.status_label.config(text="⏳ 正在获取合集信息...")
            
            ydl_opts = self.get_ydl_opts()
            ydl_opts['outtmpl'] = 'downloads/%(playlist_title)s/%(title)s.%(ext)s'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            filename = ydl.prepare_filename(entry)
                            mp3_file = filename.rsplit('.', 1)[0] + '.mp3'
                            
                            song_info = {
                                'title': entry.get('title', '未知标题'),
                                'file': mp3_file,
                                'duration': entry.get('duration', 0)
                            }
                            
                            self.playlist.append(song_info)
                
                self.root.after(0, self.update_playlist)
                self.status_label.config(text=f"✅ 合集下载完成，共{len([e for e in info.get('entries', []) if e])}首歌曲")
                
        except Exception as e:
            error_msg = f"❌ 下载失败: {str(e)}"
            self.status_label.config(text=error_msg)
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        finally:
            self.progress.stop()
            
    def refresh_playlist(self):
        self.playlist.clear()
        self.scan_downloads_folder()
        self.status_label.config(text="🔄 播放列表已刷新")
        
    def update_playlist(self):
        self.playlist_box.delete(0, tk.END)
        for i, song in enumerate(self.playlist):
            display_name = f"{i+1}. {song['title']}"
            self.playlist_box.insert(tk.END, display_name)
            
    def on_playlist_select(self, event):
        selection = self.playlist_box.curselection()
        if selection:
            self.current_index = selection[0]
            
    def on_double_click(self, event):
        self.play_selected()
            
    def play_selected(self):
        if not self.playlist:
            return
            
        song = self.playlist[self.current_index]
        self.current_song = song['file']
        
        try:
            pygame.mixer.music.load(self.current_song)
            pygame.mixer.music.play()
            self.is_playing = True
            self.play_btn.config(text="⏸️ 暂停")
            self.current_song_label.config(text=f"正在播放: {song['title']}")
            self.status_label.config(text=f"🎵 正在播放: {song['title']}")
            
            # 获取歌词
            self.get_lyrics(song['title'])
            
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {str(e)}")
            
    def toggle_play(self):
        if not self.current_song:
            if self.playlist:
                self.current_index = 0
                self.play_selected()
            else:
                messagebox.showinfo("提示", "播放列表为空，请先下载音乐")
            return
            
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_btn.config(text="▶️ 播放")
        else:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.play_btn.config(text="⏸️ 暂停")
            
    def previous_song(self):
        if len(self.playlist) > 1:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.playlist_box.selection_clear(0, tk.END)
            self.playlist_box.select_set(self.current_index)
            self.play_selected()
            
    def next_song(self):
        if len(self.playlist) > 1:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.playlist_box.selection_clear(0, tk.END)
            self.playlist_box.select_set(self.current_index)
            self.play_selected()
            
    def set_volume(self, value):
        volume = int(value) / 100.0
        pygame.mixer.music.set_volume(volume)
        
    def seek_music(self, value):
        # 进度跳转功能（基础实现）
        pass
            
    def update_progress(self):
        if self.is_playing:
            # 更新时间显示（简化版）
            current_time = pygame.mixer.music.get_pos() // 1000
            minutes = current_time // 60
            seconds = current_time % 60
            self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
            
        self.root.after(1000, self.update_progress)
        
    def get_lyrics(self, song_title):
        try:
            self.lyric_text.delete(1.0, tk.END)
            self.lyric_text.insert(tk.END, f"🔍 正在为《{song_title}》查找歌词...\n\n请稍候...")
            
            # 在新线程中获取歌词
            threading.Thread(target=self._get_lyrics_thread, args=(song_title,), daemon=True).start()
            
        except Exception as e:
            self.lyric_text.delete(1.0, tk.END)
            self.lyric_text.insert(tk.END, f"❌ 获取歌词失败: {str(e)}")
    
    def _get_lyrics_thread(self, song_title):
        try:
            lyrics = self.lyric_fetcher.get_lyrics(song_title)
            self.root.after(0, lambda: self._display_lyrics(lyrics))
        except Exception as e:
            self.root.after(0, lambda: self._display_lyrics(f"❌ 获取歌词时出错: {str(e)}"))
    
    def _display_lyrics(self, lyrics):
        self.lyric_text.delete(1.0, tk.END)
        self.lyric_text.insert(tk.END, lyrics)
        
    def remove_song(self):
        selection = self.playlist_box.curselection()
        if selection:
            index = selection[0]
            song = self.playlist[index]
            
            # 从播放列表移除
            self.playlist.pop(index)
            self.update_playlist()
            
            # 如果删除的是当前播放的歌曲，停止播放
            if self.current_song == song['file']:
                pygame.mixer.music.stop()
                self.current_song = None
                self.is_playing = False
                self.play_btn.config(text="▶️ 播放")
                self.current_song_label.config(text="当前未播放")
                
            self.status_label.config(text=f"🗑️ 已删除: {song['title']}")
            
    def clear_playlist(self):
        if not self.playlist:
            return
            
        if messagebox.askyesno("确认", "确定要清空整个播放列表吗？"):
            # 停止播放
            if self.is_playing:
                pygame.mixer.music.stop()
                self.current_song = None
                self.is_playing = False
                self.play_btn.config(text="▶️ 播放")
                self.current_song_label.config(text="当前未播放")
                
            # 清空列表
            self.playlist.clear()
            self.update_playlist()
            self.status_label.config(text="🧹 播放列表已清空")

def main():
    root = tk.Tk()
    app = BilibiliMusicPlayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
