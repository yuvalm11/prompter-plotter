import matplotlib.pyplot as plt
import cv2
import numpy as np
import os

# Get the path relative to this script file
script_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(script_dir, "../../data/28003-1740766555.webp")
image_path = os.path.normpath(image_path)

img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

def halftone_dots(img, cell_size=10, max_dot_size=10, min_dot_size=0):
    h, w = img.shape
    norm = img / 255.0
    halftone = np.ones((h, w), dtype=np.uint8) * 255
    dots = []
    for y in range(0, h, cell_size):
        for x in range(0, w, cell_size):
            cell = norm[y:y+cell_size, x:x+cell_size]
            brightness = np.mean(cell)

            radius = int((1 - brightness) * (max_dot_size / 2))
            if radius > min_dot_size:
                center = (x + cell_size // 2, y + cell_size // 2)
                cv2.circle(halftone, center, radius, 0, -1)
                dots.append((center, radius))

    return halftone, dots


cell_size = 8
max_dot_size = 10
min_dot_size = 0

halftone, dots = halftone_dots(img, cell_size=cell_size, max_dot_size=max_dot_size, min_dot_size=min_dot_size)

plt.imshow(halftone, cmap='gray')
plt.axis('off')
plt.show()

cv2.imwrite("python/drawing_code/image_dots.png", halftone)
