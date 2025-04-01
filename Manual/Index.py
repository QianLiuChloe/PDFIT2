import fitz

def mark_rectangle_in_pdf(pdf_path, output_pdf_path, page_number, point1, point2):
    """
    在指定页中添加一个矩形标注，标记由 point1 和 point2 构成的矩形范围
    """
    doc = fitz.open(pdf_path)
    try:
        page = doc[page_number]
    except IndexError:
        print(f"页码错误：PDF 只有 {len(doc)} 页")
        return

    # 计算矩形范围：取 x 和 y 的最小值和最大值
    rect = fitz.Rect(
        min(point1[0], point2[0]),
        min(point1[1], point2[1]),
        max(point1[0], point2[0]),
        max(point1[1], point2[1])
    )
    
    # 在页面上添加矩形标注（红色边框、线宽为2）
    annot = page.add_rect_annot(rect)
    annot.set_colors(stroke=(1, 0, 0))  # 红色边框
    annot.set_border(width=2)
    annot.update()

    # 保存修改后的 PDF
    doc.save(output_pdf_path)
    print("标记成功，已保存到：", output_pdf_path)

if __name__ == "__main__":
    pdf_path = input("请输入PDF文件路径：").strip()
    page_input = input("请输入页码（从1开始，默认为1）：").strip()
    page_number = int(page_input) - 1 if page_input else 0

    point1_str = input("请输入第一个坐标点（格式 x,y）：").strip()
    point2_str = input("请输入第二个坐标点（格式 x,y）：").strip()

    try:
        point1 = tuple(map(float, point1_str.split(",")))
        point2 = tuple(map(float, point2_str.split(",")))
    except Exception as e:
        print("坐标解析错误，请确保输入格式正确，例如 100,200")
        exit(1)

    output_pdf_path = "marked_output.pdf"
    mark_rectangle_in_pdf(pdf_path, output_pdf_path, page_number, point1, point2)
