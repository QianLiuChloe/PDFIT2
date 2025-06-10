import fitz
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RectangleSelector, Button
from PIL import Image, ImageDraw, ImageFont
import os
import math
import pandas as pd

# ------------------------- Parameter Setting -------------------------
zoom = 2.0  # Preview zoom ratio
mat = fitz.Matrix(zoom, zoom)
DEDUP_THRESHOLD = 5.0  # The center point distance threshold when removing duplicates, in PDF coordinates

# ------------------------- Helper Functions -------------------------
def center(coord):
    """Calculate the coordinates of the center point of the rectangle, coord is (x0, y0, x1, y1)"""
    x0, y0, x1, y1 = coord
    return ((x0 + x1) / 2, (y0 + y1) / 2)

def is_close(new_coord, existing_coords, threshold=DEDUP_THRESHOLD):
    """
    Determine whether the distance between the center point of new_coord and any center point in existing_coords is less than the threshold. 
    If so, they are considered to be the same label and True is returned.
    """
    new_center = center(new_coord)
    for coord in existing_coords:
        existing_center = center(coord)
        if math.hypot(new_center[0] - existing_center[0], new_center[1] - existing_center[1]) < threshold:
            return True
    return False

def word_in_rect(word, rect):
    """Determine whether the center point of word is within rect; the first four items of word are (x0, y0, x1, y1)"""
    x0, y0, x1, y1 = word[:4]
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    return rect.contains(fitz.Point(cx, cy))

def subtract_rect(base, sub):
    """
    Subtract the sub rectangle from the base rectangle, returning a list of the remainder (possibly 0 to 4 rectangles)
    Both are fitz.Rect objects
    """
    result = []

    if not base.intersects(sub):
        return [base]
    inter = base & sub  
 
    if inter.y0 > base.y0:
        result.append(fitz.Rect(base.x0, base.y0, base.x1, inter.y0))

    if inter.y1 < base.y1:
        result.append(fitz.Rect(base.x0, inter.y1, base.x1, base.y1))

    if inter.x0 > base.x0:
        result.append(fitz.Rect(base.x0, inter.y0, inter.x0, inter.y1))

    if inter.x1 < base.x1:
        result.append(fitz.Rect(inter.x1, inter.y0, base.x1, inter.y1))
    return result

def subtract_rects(full_rect, sub_rects):
    """
    Subtract multiple sub_rects (fitz.Rect in a list) from full_rect (fitz.Rect), returning a list of complement regions
    """
    covers = [full_rect]
    for sub in sub_rects:
        new_covers = []
        for rect in covers:
            new_covers.extend(subtract_rect(rect, sub))
        covers = new_covers
    return covers


pdf_path = input("Please enter the PDF file path：").strip()
if not os.path.exists(pdf_path):
    print("The file does not exist!")
    exit(1)

doc = fitz.open(pdf_path)
page = doc[0]  


pix = page.get_pixmap(matrix=mat)
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = img[..., :3]  


rects = []

def onselect(eclick, erelease):
    """Callback: Save the selection and draw the border when the user drags the selection"""
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    rect = {
        'x_min': min(x1, x2),
        'y_min': min(y1, y2),
        'x_max': max(x1, x2),
        'y_max': max(y1, y2)
    }
    rects.append(rect)
    print("Add a selection:", rect)
    ax.add_patch(plt.Rectangle((rect['x_min'], rect['y_min']),
                               rect['x_max'] - rect['x_min'],
                               rect['y_max'] - rect['y_min'],
                               edgecolor='red', facecolor='none', lw=2))
    plt.draw()

def finish(event):
    """Click the Finish button to end the selection."""
    print("End the selection.")
    plt.close()

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)  
ax.imshow(img)
ax.set_title("Drag the mouse to select the area (you can select multiple areas), and click Finish to end the selection.")
toggle_selector = RectangleSelector(ax, onselect, useblit=True,
                                    button=[1],
                                    minspanx=5, minspany=5,
                                    spancoords='pixels', interactive=True)
ax_button = plt.axes([0.4, 0.05, 0.2, 0.075])
btn_finish = Button(ax_button, "Finish")
btn_finish.on_clicked(finish)
plt.show()

if not rects:
    print("No region is selected and the program exits.")
    exit(0)

# ------------------------- Area Transfer -------------------------
# Convert image coordinates to PDF coordinates (divided by zoom factor)
pdf_rects = []
for r in rects:
    x_min_pdf = r['x_min'] / zoom
    y_min_pdf = r['y_min'] / zoom
    x_max_pdf = r['x_max'] / zoom
    y_max_pdf = r['y_max'] / zoom
    pdf_rect = fitz.Rect(x_min_pdf, y_min_pdf, x_max_pdf, y_max_pdf)
    pdf_rects.append(pdf_rect)
    print("The converted PDF selection coordinates:", pdf_rect)

# ------------------------- The converted PDF selection coordinates: -------------------------
# Get all the words in the page, in the format (x0, y0, x1, y1, text, ...)
words = page.get_text("words")


dedup_occurrences = {}

for word in words:
    for rect in pdf_rects:
        if word_in_rect(word, rect):
            label = word[4].strip()
            if label == "":
                continue
            if label not in dedup_occurrences:
                dedup_occurrences[label] = []
            coord = word[:4]
            if not is_close(coord, dedup_occurrences[label], DEDUP_THRESHOLD):
                dedup_occurrences[label].append(coord)
                print(f"Label {label}，Original coordinates {coord}，Center{center(coord)}")
            break  

label_counts = {label: len(coords) for label, coords in dedup_occurrences.items()}
print("Element counting Result：", label_counts)

# ------------------------- Generate preview image-------------------------

unique_labels = list(dedup_occurrences.keys())
colors = {}
cmap = plt.get_cmap("tab10")
for i, label in enumerate(unique_labels):
    colors[label] = cmap(i % 10) 

pil_img = Image.fromarray(img)
draw = ImageDraw.Draw(pil_img)
try:
    font = ImageFont.truetype("arial.ttf", 16)
except IOError:
    font = ImageFont.load_default()


for label, boxes in dedup_occurrences.items():
   
    color = tuple(int(255 * x) for x in colors[label][:3])
    for box in boxes:
        x0 = box[0] * zoom
        y0 = box[1] * zoom
        x1 = box[2] * zoom
        y1 = box[3] * zoom
        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)
        draw.text((x0, y0), label, fill=color, font=font)

preview_image_path = "count_preview.png" 
pil_img.save(preview_image_path)
print("The count preview is saved as:", preview_image_path)


full_page = page.rect


cover_rects = subtract_rects(full_page, pdf_rects)
print("The area that needs to be covered (the complementary area)")
for cr in cover_rects:
    print(cr)

for cr in cover_rects:
    page.add_redact_annot(cr, fill=(1, 1, 1))
page.apply_redactions()
output_pdf = "output_covered.pdf"
doc.save(output_pdf)
print("A new PDF (covering the portion outside the selection) is saved as:", output_pdf)  # Covered PDF output

# ------------------------- Excel  -------------------------
df = pd.DataFrame(list(label_counts.items()), columns=["Element", "No."])
excel_path = "label_counts.xlsx"
df.to_excel(excel_path, index=False)
print("The Excel table has been saved as:", excel_path)  #Excel Output
