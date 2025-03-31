import fitz
pdf_path = 'example.pdf'
doc = fitz.open(pdf_path)


title = doc.metadata['title'] # 标题
author = doc.metadata['author'] # 作者
create_time = doc.metadata['creationDate'] # 创建时间
num_pages = doc.page_count # ⻚数
page = doc.load_page(0) # 加载第⼀⻚
page_width = page.rect.width # ⻚宽
page_height = page.rect.height # ⻚⾼

print('标题:', title)
print('作者:', author)
print('创建时间:', create_time)
print('⻚数:', num_pages)
print('⻚码:', 1)
print('⻚宽:', page_width)
print('⻚⾼:', page_height)
