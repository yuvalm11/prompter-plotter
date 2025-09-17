import cv2
import numpy as np
import matplotlib.pyplot as plt
from openai import OpenAI
import base64
import requests

client = OpenAI()

def get_image_url(prompt: str, model: str = "dall-e-2", size: str = "1024x1024") -> str:
    """
    Generate an image based on the prompt.
    The prompt would be a string that describes an object or a scene
    and will be edited to include stylistic features.
    """
    instruction = prompt
    stylistic_features = ". Make it a line drawing. keep it simple. Use a black line on a white background."
    prompt += stylistic_features

    result = client.images.generate(
        model=model,
        prompt=prompt,
        size=size
    )

    print("Generated image in URL: ", result.data[0].url)

    return result.data[0].url


def get_xys(img: np.ndarray) -> list:
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]

    contours = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]

    opt = []
    for contour in contours:
        area = cv2.contourArea(contour)
        area = area / (img.shape[0] * img.shape[1])
        if area > 1e-6:
            xs = contour[:, 0, 0]
            ys = contour[:, 0, 1]

            xs = np.append(xs, xs[0]) / img.shape[1]
            ys = 1 - np.append(ys, ys[0]) / img.shape[0]

            opt.append((xs, ys))

    return opt


if __name__ == "__main__":
    # Example usage for debugging
    img_url = get_image_url("A classy cat")
    img = requests.get(img_url).content
    img = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)

    xys = get_xys(img)

    for xy in xys:
        plt.plot(xy[0], xy[1], c='green', lw=1)
    plt.xlim((0,1))
    plt.ylim((0,1))
    plt.show()
