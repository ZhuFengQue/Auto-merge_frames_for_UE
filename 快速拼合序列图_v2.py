import os
import math
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

def natural_sort_key(s):
    """自然排序key函数，支持数字序号"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def factorize(n):
    """分解质因数并生成所有可能的排列组合"""
    factors = []
    i = 2
    while i <= n:
        if n % i == 0:
            factors.append(i)
            n = n // i
        else:
            i += 1
    
    # 生成所有可能的行列组合
    unique_factors = list(set(factors))
    combinations = set()
    for i in range(1, len(factors)+1):
        row = math.prod(factors[:i])
        col = math.prod(factors[i:]) if factors[i:] else 1
        combinations.add((row, col))
        combinations.add((col, row))
    
    # 添加近似平方数排列
    sqrt_num = int(math.sqrt(n))
    if sqrt_num == 0:
        sqrt_num = 1
    combinations.add((sqrt_num, math.ceil(n/sqrt_num)))
    
    return sorted(combinations, key=lambda x: abs(x[0]-x[1]) + x[0]*x[1])

def get_layout_options(num):
    """获取所有有效的布局选项"""
    options = set()
    # 精确因数分解
    for i in range(1, num+1):
        if num % i == 0:
            options.add((i, num//i))
    # 近似平方数
    sqrt_num = int(num**0.5)
    options.add((sqrt_num, sqrt_num + (1 if sqrt_num*sqrt_num < num else 0)))
    # 质数处理
    if len(options) == 0:
        options.add((1, num))
        options.add((math.ceil(num/2), 2))
    return sorted(options, key=lambda x: (abs(x[0]-x[1]), x[0]*x[1]))

def ask_layout_choice(options):
    """弹出布局选择对话框"""
    choice_window = tk.Toplevel()
    choice_window.title("选择排列方式")
    choice_window.geometry("300x400")
    
    selected = [None]  # 使用列表实现闭包效果
    
    header = tk.Frame(choice_window)
    header.pack(pady=5)
    tk.Label(header, text="请选择排列方式", font=('Arial', 12, 'bold')).pack()
    
    canvas = tk.Canvas(choice_window)
    scrollbar = tk.Scrollbar(canvas, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    for i, (rows, cols) in enumerate(options):
        btn = tk.Button(
            scrollable_frame,
            text=f"{rows} 行 × {cols} 列 （共 {rows*cols} 格）",
            width=30,
            command=lambda r=rows, c=cols: [selected.__setitem__(0, (r,c)), choice_window.destroy()],
            relief=tk.GROOVE
        )
        btn.pack(pady=2, padx=20, fill=tk.X)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    choice_window.wait_window()
    return selected[0]

def select_folder():
    folder_path = filedialog.askdirectory()
    if not folder_path:
        return
    
    image_files = sorted([f for f in os.listdir(folder_path) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=natural_sort_key)
    
    if not image_files:
        messagebox.showerror("错误", "文件夹中没有找到图片文件")
        return
    
    try:
        images = [Image.open(os.path.join(folder_path, img)).convert("RGBA") 
                 for img in image_files]
    except Exception as e:
        messagebox.showerror("图像错误", f"无法读取图像文件：{str(e)}")
        return
    
    # 生成布局选项
    layout_options = get_layout_options(len(image_files))
    
    # 弹出选择窗口
    selected_layout = ask_layout_choice(layout_options)
    
    if not selected_layout:
        return  # 用户取消选择
    
    merge_images(folder_path, image_files, selected_layout)

def merge_images(folder_path, image_files, layout):
    rows, cols = layout
    num_images = len(image_files)
    
    try:
        images = [Image.open(os.path.join(folder_path, img)).convert("RGBA") 
                 for img in image_files]
        width, height = images[0].size
        
        # 创建画布（自动适配宽高比）
        new_image = Image.new('RGBA', 
                            (width * cols, height * rows), 
                            (0, 0, 0, 0))
        
        # 粘贴图片
        for idx in range(rows * cols):
            row = idx // cols
            col = idx % cols
            if idx < num_images:
                new_image.paste(images[idx], (col * width, row * height))
            else:
                transparent_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                new_image.paste(transparent_img, (col * width, row * height))
        
        preview_image(new_image, width, height, rows, cols, num_images, images[0], folder_path, image_files)
        
    except Exception as e:
        messagebox.showerror("处理错误", f"合并图像时出错：{str(e)}")

def preview_image(new_image, width, height, rows, cols, num_images, first_image, folder_path, image_files):
    root = tk.Toplevel()
    root.title(f"预览合并图像 ({rows}x{cols})")
    
    # 图像显示区域
    img_frame = tk.Frame(root)
    img_frame.pack(pady=10)
    
    new_image_tk = ImageTk.PhotoImage(new_image)
    label = tk.Label(img_frame, image=new_image_tk)
    label.image = new_image_tk
    label.pack(side=tk.LEFT)
    
    # 信息面板
    info_frame = tk.Frame(root)
    info_frame.pack(pady=5)
    
    info_text = (
        f"原始图片数量：{num_images}张\n"
        f"原始分辨率：{width}x{height}\n"
        f"合并后分辨率：{width*cols}x{height*rows}\n"
        f"排列方式：{rows}行 × {cols}列\n"
        f"总单元格：{rows*cols}个"
    )
    tk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(side=tk.LEFT)
    
    # 操作按钮
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    
    tk.Button(btn_frame, text="保存", 
             command=lambda: save_merged_image(new_image),
             width=10).pack(side=tk.LEFT, padx=5)
    
    tk.Button(btn_frame, text="自动填充", 
             command=lambda: auto_fill(new_image, width, height, rows, cols, num_images, first_image, folder_path, image_files),
             width=10).pack(side=tk.LEFT, padx=5)
    
    tk.Button(btn_frame, text="重新选择", 
             command=select_folder,
             width=10).pack(side=tk.LEFT, padx=5)
    
    # 新增“颠倒顺序”按钮
    tk.Button(btn_frame, text="颠倒顺序", 
             command=lambda: reverse_order(new_image, width, height, rows, cols, num_images, first_image, folder_path, image_files),
             width=10).pack(side=tk.LEFT, padx=5)

# 新增函数：颠倒顺序
def reverse_order(new_image, width, height, rows, cols, num_images, first_image, folder_path, image_files):
    """颠倒图片排列顺序并刷新预览"""
    try:
        # 颠倒图片文件顺序
        reversed_image_files = image_files[::-1]
        
        # 重新创建画布
        reversed_image = Image.new('RGBA', (width * cols, height * rows), (0, 0, 0, 0))
        
        # 颠倒顺序粘贴图片
        for idx in range(rows * cols):
            row = idx // cols
            col = idx % cols
            if idx < num_images:
                img_path = os.path.join(folder_path, reversed_image_files[idx])
                img = Image.open(img_path).convert("RGBA")
                reversed_image.paste(img, (col * width, row * height))
            else:
                transparent_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                reversed_image.paste(transparent_img, (col * width, row * height))
        
        # 刷新预览
        preview_image(reversed_image, width, height, rows, cols, num_images, first_image, folder_path, reversed_image_files)
    except Exception as e:
        messagebox.showerror("处理错误", f"颠倒顺序时出错：{str(e)}")

def auto_fill(new_image, width, height, rows, cols, num_images, first_image, folder_path, image_files):
    """使用第一张图片填充空白"""
    for idx in range(rows * cols):
        if idx >= num_images:
            row = idx // cols
            col = idx % cols
            new_image.paste(first_image, (col * width, row * height))
    preview_image(new_image, width, height, rows, cols, num_images, first_image, folder_path, image_files)

def save_merged_image(new_image):
    save_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG 文件", "*.png"), ("JPEG 文件", "*.jpg")],
        initialfile="merged_image.png"
    )
    if save_path:
        try:
            fmt = "PNG" if save_path.lower().endswith(".png") else "JPEG"
            new_image.save(save_path, format=fmt, quality=95)
            messagebox.showinfo("保存成功", f"图片已保存至：\n{save_path}")
        except Exception as e:
            messagebox.showerror("保存失败", f"保存文件时出错：{str(e)}")

def main():
    root = tk.Tk()
    root.title("智能图像拼合工具")
    root.geometry("400x200")
    
    header = tk.Frame(root, padx=20, pady=20)
    header.pack(fill=tk.BOTH, expand=True)
    
    tk.Label(header, 
            text="智能图像拼合工具\n支持自动布局选择", 
            font=('Arial', 14), 
            justify=tk.CENTER).pack(pady=10)
    
    tk.Button(header, 
             text="选择图片文件夹", 
             command=select_folder,
             height=2, 
             width=20).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()