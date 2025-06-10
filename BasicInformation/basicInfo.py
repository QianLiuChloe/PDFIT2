import fitz
pdf_path = 'example.pdf'
doc = fitz.open(pdf_path)


title = doc.metadata['title'] 
author = doc.metadata['author'] 
create_time = doc.metadata['creationDate'] 
num_pages = doc.page_count 
page = doc.load_page(0) 
page_width = page.rect.width 
page_height = page.rect.height 

print('1:', title)
print('2', author)
print('3', create_time)
print('4', num_pages)
print('5', 1)
print('6', page_width)
print('7', page_height)
