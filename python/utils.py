import cv2
import numpy as np
import matplotlib.pyplot as plt
from openai import OpenAI
import base64
import requests
from typing import List, Tuple


client = OpenAI()

def get_image_url(prompt: str, model: str = "dall-e-2", size: str = "1024x1024") -> str:
    """
    Generate an image based on the prompt.
    The prompt would be a string that describes an object or a scene
    and will be edited to include stylistic features.
    """
    # instruction = prompt
    # stylistic_features = ". Make it a line drawing. keep it simple. Use a black line on a white background."
    # prompt += stylistic_features

    # result = client.images.generate(
    #     model=model,
    #     prompt=prompt,
    #     size=size
    # )

    # print("Generated image in URL: ", result.data[0].url)

    # return result.data[0].url
    return "https://REMOVED_SECRET_DOMAIN.blob.core.windows.net/private/org-wZmXWiEEKhBYtviUXA4xBoUp/user-IkZP1XcNbcjq10i6pQrYzD68/img-Rki4oIWd3mwJ2LchEnuuy2Lb.png?st=2025-09-30T15%3A09%3A27Z&se=2025-09-30T17%3A09%3A27Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&REMOVED_SKOID&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-09-30T16%3A09%3A27Z&ske=2025-10-01T16%3A09%3A27Z&sks=b&skv=2024-08-04&REMOVED_SIGNATURE"


def get_xys(img: np.ndarray) -> List[List[Tuple[float, float]]]:
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]

    contours = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    contours = sorted(contours, key=lambda c: cv2.contourArea(c), reverse=True)
    
    # run through contours and get the points in the following format:
    # [
    #     [(x1, y1), (x2, y2), ...], # contour 1
    #     [(x1, y1), (x2, y2), ...], # contour 2
    #     ...
    # ]
    # so len(opt) is the number of contours, and len(opt[0]) is the number of points in contour 1, and len(opt[0][0]) is 2
    opt = []
    for contour in contours:
        area = cv2.contourArea(contour) / (img.shape[0] * img.shape[1])
        if area > 1e-6 or True:
            # smooth the contour
            contour = cv2.approxPolyDP(contour, 0.0001*cv2.arcLength(contour, True), True)
            opt.append(
                [
                    (float(point[0, 0])/img.shape[1], 1 - float(point[0, 1])/img.shape[0])
                    for point in contour
                ]
            )
    return opt



if __name__ == "__main__":
    # Example usage for debugging
    img_url = get_image_url("A cartoon of a dog", model="dall-e-3")
    # img_url = "https://REMOVED_SECRET_DOMAIN.blob.core.windows.net/private/org-wZmXWiEEKhBYtviUXA4xBoUp/user-IkZP1XcNbcjq10i6pQrYzD68/img-FuyA0P3TIKxd2Exr0RU0XJDw.png?st=2025-09-29T08%3A14%3A21Z&se=2025-09-29T10%3A14%3A21Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&REMOVED_SKOID&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-09-29T09%3A14%3A21Z&ske=2025-09-30T09%3A14%3A21Z&sks=b&skv=2024-08-04&REMOVED_SIGNATURE"
    img = requests.get(img_url).content
    img = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)

    xys = get_xys(img)

    points = [(x, y) for contour in xys for x, y in contour]
    minx, miny = min(x for x,y in points), min(y for x,y in points)
    maxx, maxy = max(x for x,y in points), max(y for x,y in points)
    width, height = maxx - minx, maxy - miny

    scale = 235 / max(width, height)
    scaled = [[((x - minx) * scale, (y - miny) * scale) for x, y in contour] for contour in xys]
    
    offset = (235 - min(width, height) * scale) / 2
    if width > height:
        scaled_xys = [[(x, y + offset) for x, y in contour] for contour in scaled]
    else:
        scaled_xys = [[(x + offset, y) for x, y in contour] for contour in scaled]

    for contour in scaled_xys:
        contour.append(contour[0])  # close the contour
        for point in contour:
            x = round(point[0])
            y = round(point[1])
            plt.plot(x, y, 'r.', markersize=1)

    plt.xlim(0, 235)
    plt.ylim(0, 235)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
