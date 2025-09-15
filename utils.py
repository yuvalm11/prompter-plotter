import cv2
import numpy as np
import matplotlib.pyplot as plt


def get_image(prompt: str) -> np.ndarray:
    """
    Generate an image based on the prompt.
    The prompt would be a string that describes an object or a scene
    and will be edited to include stylistic features.
    """
    instruction = prompt
    stylistic_features = ". Make it a line drawing. keep it simple. Use a black line on a white background."
    prompt += stylistic_features 

    # TODO: Implement a call to a generative model to generate the image.
    img = cv2.imread("./data/cat.webp")
    return img


def get_xys(img: np.ndarray) -> list:
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]

    contours = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    areas = [cv2.contourArea(contour) for contour in contours]
    contours = [contour for contour, area in sorted(zip(contours, areas), key=lambda x: x[1], reverse=True)]

    opt = []
    for contour in contours:
        xs = contour[:, 0, 0]
        ys = contour[:, 0, 1]

        xs = np.append(xs, xs[0]) #/ 1024
        ys = 1024 - np.append(ys, ys[0]) #/ 1024

        opt.append((xs, ys))

    return opt


# Example usage
img = get_image("A cat")
plt.imshow(img, origin='upper', extent=(1024, img.shape[1]*2, 0, img.shape[0]))

xys = get_xys(img)
for xy in xys:
    plt.plot(xy[0], xy[1], c='green', lw=1)

plt.xlim((0,2048))
plt.ylim((0,1024))
plt.show()
