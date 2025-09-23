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
    contours = sorted(contours, key=lambda c: cv2.contourArea(c), reverse=True)
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
    # img_url = get_image_url("An elephant in the jungle", model="dall-e-3")
    img_url = "https://REMOVED_SECRET_DOMAIN.blob.core.windows.net/private/org-wZmXWiEEKhBYtviUXA4xBoUp/user-IkZP1XcNbcjq10i6pQrYzD68/img-Df4cekH0PWUNqS6uon5igEgk.png?st=2025-09-23T19%3A51%3A10Z&se=2025-09-23T21%3A51%3A10Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=1726b4ce-fee1-450b-8b92-1731ad8745f6&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-09-23T20%3A51%3A10Z&ske=2025-09-24T20%3A51%3A10Z&sks=b&skv=2024-08-04&sig=CKIxdeE9D8C4/u8pfq2dQ5zACu4F1giDYXyGE4uHT38%3D"
    img = requests.get(img_url).content
    img = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)

    xys = get_xys(img)

    for x, y in xys:
        plt.plot(x, y, c='green', lw=2)
    plt.xlim((0,1))
    plt.ylim((0,1))
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
