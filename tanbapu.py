import requests
import urllib3
import time
import re
import io
import os
import tkinter as tk
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from tkinter import ttk, messagebox
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_js(url, normalize=True):
    """
    从指定的乐谱页面获取简谱图片URL列表和页面ID

    参数:
        url (str): 乐谱页面URL，例如 "https://www.tan8.com/yuepu-118972.html"
        normalize (bool): 是否进行URL规范化

    返回:
        tuple: (page_id, img_urls)
            page_id (str): 从URL中提取的数字ID，如 "118972"
            img_urls (list): 处理后的图片URL列表
    """
    # 提取页面ID（URL中的数字部分）
    page_id_match = re.search(r'yuepu-(\d+)', url)
    page_id = page_id_match.group(1) if page_id_match else "unknown"

    driver = webdriver.Chrome()
    try:
        driver.get(url)
        time.sleep(3)

        yuepuArrJian = driver.execute_script("return yuepuArrJian;")

        img_urls = []
        # 兼容不同的数据结构
        if isinstance(yuepuArrJian, list):
            for item in yuepuArrJian:
                if isinstance(item, dict) and 'img' in item:
                    img_val = item['img']
                    if isinstance(img_val, list):
                        img_urls.extend(img_val)
                    elif isinstance(img_val, str):
                        img_urls.append(img_val)
        elif isinstance(yuepuArrJian, dict) and 'img' in yuepuArrJian:
            img_val = yuepuArrJian['img']
            if isinstance(img_val, list):
                img_urls.extend(img_val)
            elif isinstance(img_val, str):
                img_urls.append(img_val)
        elif isinstance(yuepuArrJian, str):
            img_urls.append(yuepuArrJian)

        # 去重
        seen = set()
        unique_urls = []
        for u in img_urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)

        if normalize:
            unique_urls = [normalize_image_url(u) for u in unique_urls]

        return page_id, unique_urls
    except Exception as e:
        print(f"获取失败: {e}")
        return page_id, []
    finally:
        driver.quit()

#GUI界面，用于获取id
def get_id_from_gui():
    """
    弹出高级风格 GUI 窗口，让用户输入乐谱 ID（纯数字）。
    返回用户输入的 ID（字符串）；若用户取消或关闭窗口，返回 None。
    """
    result = None

    def on_submit():
        nonlocal result
        user_id = entry.get().strip()
        if not user_id:
            messagebox.showwarning("输入为空", "ID 不能为空，请重新输入！")
            return
        if not user_id.isdigit():
            messagebox.showwarning("格式错误", "ID 必须为纯数字！\n例如：118972")
            return
        result = user_id
        root.destroy()

    def on_cancel():
        nonlocal result
        result = None
        root.destroy()

    root = tk.Tk()
    root.title("输入乐谱 ID")
    root.geometry("440x280")
    root.resizable(False, False)

    # 窗口居中
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')

    bg_color = "#f5f7fa"
    root.configure(bg=bg_color)

    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Accent.TButton",
                    font=("Segoe UI", 10, "bold"),
                    background="#0078d7",
                    foreground="white",
                    borderwidth=0,
                    focusthickness=0,
                    padding=6)
    style.map("Accent.TButton",
              background=[("active", "#005a9e")],
              foreground=[("active", "white")])

    style.configure("Secondary.TButton",
                    font=("Segoe UI", 10),
                    background="#e0e0e0",
                    foreground="#333333",
                    borderwidth=0,
                    padding=6)
    style.map("Secondary.TButton",
              background=[("active", "#c0c0c0")])

    # 标题
    title_label = tk.Label(root, text="乐谱 ID 输入",
                           font=("Segoe UI", 16, "bold"),
                           fg="#2c3e50", bg=bg_color)
    title_label.grid(row=0, column=0, columnspan=2, pady=(20, 5), padx=20, sticky="w")

    # 描述
    desc_label = tk.Label(root, text="请输入乐谱 URL 中的纯数字 ID（例如：118972）",
                          font=("Segoe UI", 11),
                          fg="#7f8c8d", bg=bg_color)
    desc_label.grid(row=1, column=0, columnspan=2, pady=(0, 15), padx=20, sticky="w")

    # ID 标签
    id_label = tk.Label(root, text="ID",
                        font=("Segoe UI", 11, "bold"),
                        fg="#2c3e50", bg=bg_color)
    id_label.grid(row=2, column=0, padx=(20, 5), pady=(0, 5), sticky="e")

    # 输入框
    entry = tk.Entry(root, font=("Segoe UI", 11),
                     highlightthickness=1,
                     highlightcolor="#0078d7",
                     highlightbackground="#d0d0d0",
                     relief="flat", bd=0, bg="white")
    entry.grid(row=2, column=1, padx=(0, 20), pady=(0, 5), sticky="ew")
    entry.focus_set()

    # 按钮框架
    button_frame = tk.Frame(root, bg=bg_color)
    button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 20), padx=20, sticky="ew")

    submit_btn = ttk.Button(button_frame, text="✓ 提 交", style="Accent.TButton",
                            command=on_submit, width=12)
    submit_btn.pack(side="right", padx=(10, 0))

    cancel_btn = ttk.Button(button_frame, text="✗ 取 消", style="Secondary.TButton",
                            command=on_cancel, width=12)
    cancel_btn.pack(side="right")

    # 绑定键盘事件
    root.bind("<Return>", lambda event: on_submit())
    root.bind("<Escape>", lambda event: on_cancel())

    # 让输入框列可拉伸
    root.grid_columnconfigure(1, weight=1)

    root.mainloop()
    return result

#规范url格式
def normalize_image_url(url):
    """
    规范化图片URL：
    - 将路径中的双斜杠替换为单斜杠
    - 将文件名中的 'prev_数字' 替换为目录标识符
    - 将 '.jianpu.' 替换为 '.ypad.'
    """
    # 分离协议
    if url.startswith('https://'):
        protocol = 'https://'
        rest = url[8:]
    elif url.startswith('http://'):
        protocol = 'http://'
        rest = url[7:]
    else:
        protocol = ''
        rest = url
    # 替换双斜杠
    rest = rest.replace('//', '/')
    # 提取目录标识符
    dir_match = re.search(r'/([^/]+)_jianpu/', rest)
    if dir_match:
        identifier = dir_match.group(1)
        # 替换文件名中的 prev_数字
        rest = re.sub(r'prev_\d+', identifier, rest)
        # 替换 .jianpu. 为 .ypad.
        rest = rest.replace('.jianpu.', '.ypad.')
    return protocol + rest

#获取图片页数
def get_page_info(url):
    driver = webdriver.Chrome()
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        
        yuepuArrJian = driver.execute_script("return window.yuepuArrJian;")
        # 不再依赖 page_count，但保留以防万一
        page_count = driver.execute_script("return window.page_count;")
        if page_count is None:
            page_count = 1
        
        page_id_match = re.search(r'yuepu-(\d+)', url)
        page_id = page_id_match.group(1) if page_id_match else "unknown"
        
        # 提取第一张图片原始URL
        if not yuepuArrJian:
            raise Exception("未找到 yuepuArrJian")
        if isinstance(yuepuArrJian, list) and len(yuepuArrJian) > 0:
            first_url = yuepuArrJian[0].get('img', [None])[0]
        elif isinstance(yuepuArrJian, dict):
            first_url = yuepuArrJian.get('img', [None])[0] if isinstance(yuepuArrJian.get('img'), list) else yuepuArrJian.get('img')
        else:
            first_url = None
        if not first_url:
            raise Exception("无法提取图片URL")
        
        # 规范化
        normalized = normalize_image_url(first_url)
        # 生成模板，例如将 ".0.png" 替换为 ".{page}.png"
        # 注意：需要精确匹配数字
        template = re.sub(r'\.(\d+)\.png', '.{page}.png', normalized)
        return page_id, page_count, template
    finally:
        driver.quit()

#探测函数
def generate_urls_by_detection(template_url, max_pages=20):
    urls = []
    for page in range(max_pages):
        test_url = template_url.format(page=page)
        try:
            # 使用 GET 流式请求，只读取头部，节省带宽
            resp = requests.get(test_url, verify=False, timeout=8, stream=True)
            if resp.status_code == 200:
                urls.append(test_url)
                resp.close()
            else:
                # 第一页失败则终止
                if page == 0:
                    print(f"警告：第一张图片返回 {resp.status_code}，请检查模板")
                break
        except Exception as e:
            print(f"探测第 {page} 页时出错: {e}")
            break
    return urls

#生成图片url列表
def generate_all_urls(template_url, page_count):
    """
    根据模板和页数生成所有图片URL列表
    template_url: 包含 {page} 占位符的字符串
    page_count: 总页数（从1开始或从0开始？根据常见情况，图片序号从0开始）
    """
    urls = []
    for page_num in range(page_count):  # 假设第一页序号为0，第二页为1...
        url = template_url.format(page=page_num)
        urls.append(url)
    return urls

#下载图片，并且保存为灰度
def download_all_images(page_id, img_urls, save_dir="output_images", verify_ssl=False):
    """
    下载所有图片，转为灰度PNG，文件名: {page_id}_{序号}.png
    """
    if not img_urls:
        print("没有图片需要下载")
        return []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Referer': 'https://www.tan8.com/',
    }
    
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500,502,503,504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    
    os.makedirs(save_dir, exist_ok=True)
    saved = []
    
    for idx, url in enumerate(img_urls):
        try:
            print(f"下载 {idx+1}/{len(img_urls)}: {url}")
            resp = session.get(url, headers=headers, timeout=15, verify=verify_ssl)
            resp.raise_for_status()
            
            img = Image.open(io.BytesIO(resp.content))
            # 处理透明背景并转灰度
            if img.mode in ('RGBA', 'LA', 'P'):
                bg = Image.new('RGB', img.size, (255,255,255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                mask = img.split()[-1] if img.mode == 'RGBA' else None
                bg.paste(img, mask=mask)
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            gray = img.convert('L')
            
            filename = f"{page_id}_{idx}.png"
            filepath = os.path.join(save_dir, filename)
            gray.save(filepath, 'PNG')
            print(f"保存成功: {filepath}")
            saved.append(filepath)
        except Exception as e:
            print(f"失败 {url}: {e}")
    
    print(f"完成，成功 {len(saved)}/{len(img_urls)}")
    session.close()
    return saved

# 主函数
def main(url):
    page_url = url  # 可改为任意乐谱页面
    page_id, _, template = get_page_info(page_url)
    print(f"页面ID: {page_id}")
    print(f"URL模板: {template}")
    
    all_urls = generate_urls_by_detection(template, max_pages=20)
    print(f"共发现 {len(all_urls)} 张图片")
    for i, u in enumerate(all_urls):
        print(f"  {i}: {u}")
    
    if all_urls:
        download_all_images(page_id, all_urls, save_dir=f"output_{page_id}", verify_ssl=False)
    else:
        print("没有找到任何有效图片")

if __name__ == '__main__':
    #谱地址
    #html_content = fetch_page_with_headers("https://www.tan8.com/yuepu-118972.html")
    user_id = get_id_from_gui()
    if user_id:
        print(f"✓ main 函数收到的 ID 是：{user_id}")
        # 在这里可以对 ID 进行后续处理，如数据库查询、API 调用等
        url = "https://www.tan8.com/yuepu-{}.html".format(user_id)    
        main(url)
    else:
        print("✗ 用户取消了输入或关闭了窗口")

