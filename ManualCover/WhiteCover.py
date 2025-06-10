import fitz  
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RectangleSelector, Button

zoom = 2.0
mat = fitz.Matrix(zoom, zoom)

pdf_path = input("APTH:")
doc = fitz.open(pdf_path)
page = doc[0] 


pix = page.get_pixmap(matrix=mat)
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
        img = img[..., :3]  

rects = []

def onselect(eclick, erelease):

    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    rect = {
        'x_min': min(x1, x2),
        'y_min': min(y1, y2),
        'x_max': max(x1, x2),
        'y_max': max(y1, y2)
    }
    rects.append(rect)
    print("ADD", rect)

    ax.add_patch(plt.Rectangle((rect['x_min'], rect['y_min']),
                               rect['x_max'] - rect['x_min'],
                               rect['y_max'] - rect['y_min'],
                               edgecolor='red', facecolor='none', lw=2))
    plt.draw()

def finish(event):

    print("FINSISH")
    plt.close()


fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2) 
ax.imshow(img)
ax.set_title("FINSISH")

toggle_selector = RectangleSelector(ax, onselect, useblit=True,
                                    button=[1], 
                                    minspanx=5, minspany=5,
                                    spancoords='pixels',
                                    interactive=True)


ax_button = plt.axes([0.4, 0.05, 0.2, 0.075])
btn_finish = Button(ax_button, "Finish")
btn_finish.on_clicked(finish)

plt.show()

if rects:
    pdf_rects = []
    for r in rects:
   
        x_min_pdf = r['x_min'] / zoom
        y_min_pdf = r['y_min'] / zoom
        x_max_pdf = r['x_max'] / zoom
        y_max_pdf = r['y_max'] / zoom
        pdf_rect = fitz.Rect(x_min_pdf, y_min_pdf, x_max_pdf, y_max_pdf)
        pdf_rects.append(pdf_rect)
        print("AFTER: ", pdf_rect)
    

    for rect in pdf_rects:
        page.add_redact_annot(rect, fill=(1, 1, 1)) 

    page.apply_redactions()

    output_pdf = "output_2.pdf"
    doc.save(output_pdf)
    print("SAVED：", output_pdf)
else:
    print("NO SELECTED")
