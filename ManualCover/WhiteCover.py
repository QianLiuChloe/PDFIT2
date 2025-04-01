import fitz  # PyMuPDF，用于处理 PDF
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RectangleSelector, Button

# 设置缩放比例（预览时放大页面，便于选区）
zoom = 2.0
mat = fitz.Matrix(zoom, zoom)

# 用户输入 PDF 文件路径
pdf_path = input("请输入PDF文件路径：")
doc = fitz.open(pdf_path)
page = doc[0]  # 这里只处理第一页，如需多页请循环处理

# 渲染 PDF 页面为图像
pix = page.get_pixmap(matrix=mat)
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = img[..., :3]  # 如果存在 alpha 通道，则取前三个通道

# 用于存储用户选取的所有矩形区域（图像坐标）
rects = []

def onselect(eclick, erelease):
    """
    当用户在预览图上拖拽选择矩形区域后调用，将选区信息保存，并在图上绘制红色边框作为反馈
    """
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    rect = {
        'x_min': min(x1, x2),
        'y_min': min(y1, y2),
        'x_max': max(x1, x2),
        'y_max': max(y1, y2)
    }
    rects.append(rect)
    print("添加选区：", rect)
    # 在图上绘制矩形边框
    ax.add_patch(plt.Rectangle((rect['x_min'], rect['y_min']),
                               rect['x_max'] - rect['x_min'],
                               rect['y_max'] - rect['y_min'],
                               edgecolor='red', facecolor='none', lw=2))
    plt.draw()

def finish(event):
    """
    点击 Finish 按钮后结束选区，关闭交互窗口
    """
    print("结束选区。")
    plt.close()

# 创建预览图和选区工具
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)  # 为按钮留出空间
ax.imshow(img)
ax.set_title("拖动鼠标框选多个区域，选完后点击 Finish 按钮结束选区")

# 创建交互式矩形选择器（不再使用 drawtype 参数，兼容性更好）
toggle_selector = RectangleSelector(ax, onselect, useblit=True,
                                    button=[1],  # 仅左键生效
                                    minspanx=5, minspany=5,
                                    spancoords='pixels',
                                    interactive=True)

# 添加 Finish 按钮
ax_button = plt.axes([0.4, 0.05, 0.2, 0.075])
btn_finish = Button(ax_button, "Finish")
btn_finish.on_clicked(finish)

plt.show()

# 如果用户选取了区域，则对 PDF 进行处理
if rects:
    pdf_rects = []
    for r in rects:
        # 将图像像素坐标转换回 PDF 坐标（除以 zoom 缩放比例）
        x_min_pdf = r['x_min'] / zoom
        y_min_pdf = r['y_min'] / zoom
        x_max_pdf = r['x_max'] / zoom
        y_max_pdf = r['y_max'] / zoom
        pdf_rect = fitz.Rect(x_min_pdf, y_min_pdf, x_max_pdf, y_max_pdf)
        pdf_rects.append(pdf_rect)
        print("转换后的 PDF 区域坐标：", pdf_rect)
    
    # 对页面中每个指定区域添加 redaction 注释，填充白色以覆盖内容
    for rect in pdf_rects:
        page.add_redact_annot(rect, fill=(1, 1, 1))  # 白色填充
    # 应用所有 redaction 注释，将内容删除/覆盖
    page.apply_redactions()
    
    # 保存新的 PDF 文档
    output_pdf = "output_2.pdf"
    doc.save(output_pdf)
    print("新的 PDF 已保存为：", output_pdf)
else:
    print("未选择任何区域。")
