import matplotlib.pyplot as plt
import numpy as np
import cv2

box_height = 7
box_width = 1
min_freq = 2
max_freq = 6
num_points = 2

img = cv2.imread("python/svg/test_files/Unknown-2.png", cv2.IMREAD_GRAYSCALE)
scale = 235 / max(img.shape)
img = cv2.resize(img, (0,0), fx=scale, fy=scale)
img = cv2.copyMakeBorder(img, 0, box_height - img.shape[0] % box_height, 0, box_width - img.shape[1] % box_width, cv2.BORDER_CONSTANT, value=[255, 255, 255])

for y in range(0, img.shape[0], box_height):
    for x in range(0, img.shape[1], box_width):
        box = img[y:y+box_height, x:x+box_width]
        avg_color = np.mean(box)
        box[:] = avg_color


img = 255 - img
# normalize to min_freq to max_freq with only even numbers
img = cv2.normalize(img, None, min_freq, max_freq, cv2.NORM_MINMAX)
img = img.astype(np.int32)
img = img - img % 2

pic_width = img.shape[1]-1
pic_height = img.shape[0]-1
xs = np.array([])
ys = np.array([])

for y_start in range(0, pic_height, box_height):
    if y_start % 2 == 0:
        for x_start in range(0, pic_width, box_width):
            freq = img[y_start, x_start]
            x = np.linspace(x_start, x_start+box_width, num_points)
            y = (np.sin(freq * np.pi * x / box_height) + 1) * box_height / 2 + y_start
            xs = np.concatenate((xs, x))
            ys = np.concatenate((ys, y))
    else:
        for x_start in range(pic_width, 0, -box_width):
            freq = img[y_start, x_start]
            x = np.linspace(x_start, x_start-box_width, num_points)
            y = (np.sin(freq * np.pi * x / box_height) + 1) * box_height / 2 + y_start
            xs = np.concatenate((xs, x))
            ys = np.concatenate((ys, y))


plt.plot(xs, ys, linewidth=1.2)
plt.gca().invert_yaxis()
plt.show()