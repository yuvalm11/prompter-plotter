import cv2
import numpy as np
import matplotlib.pyplot as plt


def get_image(prompt: str) -> np.ndarray:
    """
    Use DALL-E to generate an image based on the prompt.
    The prompt would be a string that describes an object or a scene
    and will be edited to include stylistic featurs.
    """
    instruction = "Generate an image of a " + prompt
    stylistic_features = ". Make it a line drawing. keep it simple. Use a black line on a white background."
    prompt += stylistic_features 
    raise NotImplementedError


def get_xys(img: np.ndarray) -> list:
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]

    contours = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    areas = [cv2.contourArea(contour) for contour in contours]
    contours = [contour for contour, area in sorted(zip(contours, areas), key=lambda x: x[1], reverse=True)][:19*len(areas) // 20]

    opt = []
    for contour in contours:
        xs = contour[:, 0, 0]
        ys = contour[:, 0, 1]

        xs = np.append(xs, xs[0]) / 1024
        ys = 1 - np.append(ys, ys[0]) / 1024

        opt.append((xs, ys))

    return opt


# Example usage
img = cv2.imread("data/cat.webp") # Replace with get_image("cat") when implemented

xys = get_xys(img)
for xy in xys:
    plt.plot(xy[0], xy[1], c='black', lw=1)

print(xys)
plt.show()
