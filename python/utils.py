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
    instruction = prompt
    stylistic_features = ". Make it a line drawing. keep it very simple. Use a black line on a white background."
    prompt += stylistic_features

    result = client.images.generate(
        model=model,
        prompt=prompt,
        size=size
    )

    print("Generated image in URL: ", result.data[0].url)

    return result.data[0].url
    # return "https://REMOVED_SECRET_DOMAIN.blob.core.windows.net/private/org-wZmXWiEEKhBYtviUXA4xBoUp/user-IkZP1XcNbcjq10i6pQrYzD68/img-bVhVMwuDEOJLfp6GFPjLbCAM.png?st=2025-11-02T16%3A14%3A25Z&se=2025-11-02T18%3A14%3A25Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&REMOVED_SKOID&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-11-02T17%3A14%3A25Z&ske=2025-11-03T17%3A14%3A25Z&sks=b&skv=2024-08-04&REMOVED_SIGNATURE"


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


def scale_paths(xys: List[List[Tuple[float, float]]], target_extent: float) -> List[List[Tuple[float, float]]]:
    """
    Scale contours to fit within a square of size target_extent while preserving aspect ratio
    and centering along the shorter dimension.
    """
    if not xys:
        return []

    points = [(x, y) for contour in xys for x, y in contour]
    minx, miny = min(x for x, y in points), min(y for x, y in points)
    maxx, maxy = max(x for x, y in points), max(y for x, y in points)
    width, height = maxx - minx, maxy - miny

    if width == 0 and height == 0:
        return [[(0.0, 0.0) for _ in contour] for contour in xys]

    scale = float(target_extent) / max(width, height)
    scaled = [[((x - minx) * scale, (y - miny) * scale) for x, y in contour] for contour in xys]

    offset = (float(target_extent) - min(width, height) * scale) / 2
    if width > height:
        scaled_xys = [[(x, y + offset) for x, y in contour] for contour in scaled]
    else:
        scaled_xys = [[(x + offset, y) for x, y in contour] for contour in scaled]

    min_dist = 0.5
    final_xys = []
    for contour in scaled_xys:
        contour.append(contour[0])
        last_point = contour[0]
        final_contour = []
        for point in contour:
            dist = np.linalg.norm(np.array(point) - np.array(last_point))
            if dist > min_dist:
                final_contour.append(point)
                last_point = point
        final_xys.append(final_contour)

    return final_xys


if __name__ == "__main__":
    # Example usage for debugging
    img_url = get_image_url("A happy cartoon rhino", model="dall-e-3")
    img = requests.get(img_url).content
    img = cv2.imdecode(np.frombuffer(img, dtype=np.uint8), cv2.IMREAD_COLOR)

    xys = get_xys(img)

    scaled_xys = scale_paths(xys, 235)

    for contour in scaled_xys:
        contour.append(contour[0])  # close the contour
        xs = []
        ys = []
        for point in contour:
            xs.append(point[0])
            ys.append(point[1])
        plt.plot(xs, ys, 'black', linewidth=0.5)

    plt.xlim(0, 235)
    plt.ylim(0, 235)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
