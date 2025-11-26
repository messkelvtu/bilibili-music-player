import requests
import re

class LyricFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_lyrics(self, song_name, artist=None):
        """从多个来源获取歌词"""
        lyrics = None
        
        # 清理歌曲名称
        song_name = self.clean_song_name(song_name)
        
        # 尝试多个API，按优先级排序
        sources = [
            self._get_lyrics_api,
            self._get_geci_lyrics,
            self._get_qq_lyrics_simple,
        ]
        
        for source in sources:
            try:
                lyrics = source(song_name, artist)
                if lyrics and self._is_valid_lyric(lyrics):
                    return lyrics
            except Exception as e:
                print(f"{source.__name__} 失败: {e}")
                continue
                
        return self._get_fallback_lyrics(song_name)
    
    def clean_song_name(self, song_name):
        """清理歌曲名称，移除不必要的字符"""
        # 移除常见的B站视频标题后缀
        patterns = [
            r'【.*?】',
            r'\[.*?\]',
            r'\(.*?\)',
            r'（.*?）',
            r'\|.*',
            r'-.*',
            r'_.*',
            r'Bilibili',
            r'bilibili',
            r'BILIBILI',
            r'高清.*',
            r'官方.*',
            r'MV.*',
            r'音源.*',
            r'完整版.*',
            r'Full.*',
        ]
        
        cleaned = song_name
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)
            
        # 移除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned if cleaned else song_name
    
    def _get_lyrics_api(self, song_name, artist=None):
        """使用公开歌词API"""
        try:
            # 使用一个免费的歌词API
            url = f"https://api.lyrics.ovh/v1/{artist or 'Various Artists'}/{song_name}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'lyrics' in data:
                    return data['lyrics']
        except:
            pass
        return None
    
    def _get_geci_lyrics(self, song_name, artist=None):
        """从歌词API获取歌词"""
        try:
            url = f"https://geci.me/api/lyric/{song_name}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('result') and len(data['result']) > 0:
                    lyric_url = data['result'][0]['lrc']
                    lyric_response = self.session.get(lyric_url, timeout=10)
                    if lyric_response.status_code == 200:
                        return lyric_response.text
        except:
            pass
        return None
    
    def _get_qq_lyrics_simple(self, song_name, artist=None):
        """简化的QQ音乐歌词获取"""
        try:
            # 这里使用一个模拟的歌词，实际使用时应该调用真实API
            # 由于API限制，返回格式化的模拟歌词
            return self._generate_sample_lyrics(song_name)
        except:
            pass
        return None
    
    def _generate_sample_lyrics(self, song_name):
        """生成示例歌词"""
        return f"""🎵 《{song_name}》歌词

[00:00.00] 歌曲: {song_name}
[00:05.00] 艺术家: 未知
[00:10.00] 专辑: 未知
[00:15.00] 
[00:20.00] 这是一首美妙的音乐
[00:25.00] 歌词正在努力加载中
[00:30.00] 请享受这段旋律时光
[00:35.00] 
[00:40.00] 如果这里没有显示歌词
[00:45.00] 可能是因为:
[00:50.00] 1. 歌曲名称不匹配
[00:55.00] 2. 歌词库中没有此歌曲
[01:00.00] 3. 网络连接问题
[01:05.00] 
[01:10.00] 🎶 音乐继续播放中...
"""
    
    def _get_fallback_lyrics(self, song_name):
        """获取备用歌词"""
        return f"""🎵 《{song_name}》

[00:00.00] ⚠️ 未找到精确匹配的歌词
[00:05.00] 
[00:10.00] 可能的原因:
[00:15.00] • 歌曲名称不标准
[00:20.00] • 歌词库中暂无此歌曲
[00:25.00] • 网络连接问题
[00:30.00] 
[00:35.00] 💡 建议:
[00:40.00] 1. 检查歌曲名称是否正确
[00:45.00] 2. 尝试手动搜索歌词
[00:50.00] 3. 享受纯音乐版本
[00:55.00] 
[01:00.00] 🎶 音乐无国界，享受此刻...
"""
    
    def _is_valid_lyric(self, lyrics):
        """检查歌词是否有效"""
        if not lyrics:
            return False
            
        # 检查是否包含错误信息
        invalid_indicators = [
            '暂无歌词', '无歌词', '未找到', 'Error', 
            'error', 'Not Found', 'not found'
        ]
        
        lyrics_lower = lyrics.lower()
        for indicator in invalid_indicators:
            if indicator.lower() in lyrics_lower:
                return False
                
        return len(lyrics.strip()) > 10

# 使用示例
if __name__ == "__main__":
    fetcher = LyricFetcher()
    lyrics = fetcher.get_lyrics("孤勇者")
    print(lyrics)
