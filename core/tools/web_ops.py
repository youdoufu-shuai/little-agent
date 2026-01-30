import json
import requests
import os
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def search_web(query: str, max_results: int = 5) -> str:
    """
    使用 DuckDuckGo 搜索网络。
    
    Args:
        query: 搜索查询。
        max_results: 返回的最大结果数（默认为 5）。
        
    Returns:
        搜索结果的 JSON 字符串。
    """
    try:
        results = []
        try:
            with DDGS() as ddgs:
                # text() 方法返回一个迭代器
                for r in ddgs.text(query, max_results=max_results):
                    results.append(r)
        except Exception as e:
            # Fallback to googlesearch-python if DDGS fails
            print(f"DDGS failed: {e}, falling back to googlesearch")
            results = []
        
        if not results:
            # Fallback logic
            try:
                from googlesearch import search
                # googlesearch.search yields urls. We need to fetch titles/snippets if possible, 
                # but googlesearch-python simple search only returns URLs.
                # However, there is 'advanced=True' in some versions, but 1.3.0 might be basic.
                # Let's check if we can get more info.
                # If not, we just return URLs and let the agent read them.
                g_results = search(query, num_results=max_results, advanced=True)
                for r in g_results:
                    results.append({
                        "title": r.title,
                        "href": r.url,
                        "body": r.description
                    })
            except ImportError:
                return json.dumps([{"error": "Google search fallback not available"}], ensure_ascii=False)
            except Exception as e:
                return f"搜索网络出错 (Google Fallback): {str(e)}"

        if not results:
            return json.dumps([{"error": "No results found. Search engines might be blocking requests from this IP."}], ensure_ascii=False)

        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return f"搜索网络出错: {str(e)}"

def read_url(url: str) -> str:
    """
    获取并读取网页的主要文本内容，包括图像链接。
    
    Args:
        url: 要读取的网页 URL。
        
    Returns:
        提取的网页文本内容和图像链接。
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 清理前提取图像
        image_list = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
                
            # 处理相对 URL
            if src.startswith('//'):
                src = 'https:' + src
            elif not src.startswith(('http://', 'https://')):
                src = urljoin(url, src)
            
            alt = img.get('alt', 'Image')
            img_md = f"![{alt}]({src})"
            if img_md not in image_list:
                image_list.append(img_md)

        # 移除脚本和样式元素
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        # 获取文本
        text = soup.get_text()
        
        # 分行并去除每行的首尾空格
        lines = (line.strip() for line in text.splitlines())
        # 将多标题行分解为单行
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # 丢弃空行
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # 限制文本长度以避免上下文溢出（约 10k 字符）
        if len(text) > 10000:
            text = text[:10000] + "\n...(内容已截断)..."
            
        # 追加找到的图像
        if image_list:
            text += "\n\n[找到的图像 (前 20 个)]:\n" + "\n".join(image_list[:20])

        return text
    except Exception as e:
        return f"读取 URL 出错: {str(e)}"

def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息。
    
    Args:
        city: 城市名称（例如 "Shanghai" 或 "Beijing"）。
        
    Returns:
        包含天气信息的字符串。
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "错误: 未配置 OPENWEATHER_API_KEY 环境变量。"
        
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "zh_cn"
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            return f"{city} 天气: {weather}, 温度: {temp}°C, 湿度: {humidity}%"
        else:
            return f"获取天气失败: {data.get('message', '未知错误')}"
    except Exception as e:
        return f"请求天气 API 出错: {str(e)}"
