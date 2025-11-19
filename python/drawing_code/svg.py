import svgpathtools
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

def process_svg(file_path: str, precision = 0.3, bounding_box = (0, 235, 0, 305)):
    paths, _ = svgpathtools.svg2paths(file_path)

    if bounding_box is None:
        scale_factor = 1.0
    else:
        min_x, max_x, min_y, max_y = svgpathtools.path.Path(*paths).bbox()
        width, height = bounding_box[1] - bounding_box[0], bounding_box[3] - bounding_box[2]
        scale_factor = -abs(min(width / (max_x - min_x), height / (max_y - min_y)))


    print(f"Scaling by {scale_factor}")
    paths = [path.translated(complex(-min_x, -min_y)) for path in paths]
    paths = [path.translated(complex(-max_x, -max_y)) for path in paths]
    paths = [path.scaled(scale_factor) for path in paths]
    paths = [path.translated(complex(bounding_box[0], bounding_box[2])) for path in paths]

    min_x, max_x, min_y, max_y = svgpathtools.path.Path(*paths).bbox()

    print(f"Bounding box: {min_x}, {max_x}, {min_y}, {max_y}")

    output = []
    for path in paths:
        pts = []
        for segment in path:
            if segment.length() < precision:
                continue
            if type(segment) == svgpathtools.QuadraticBezier:
                pts += approx_quadratic_bezier(segment, precision)
            elif type(segment) == svgpathtools.CubicBezier:
                pts += approx_cubic_bezier(segment, precision)
            elif type(segment) == svgpathtools.Line:
                pts += [(segment.start.real, segment.start.imag), (segment.end.real, segment.end.imag)]
        
        if pts: output.append(pts)

    return output


def approx_quadratic_bezier(segment: svgpathtools.QuadraticBezier, precision: float):
    if precision <= 0:
        raise ValueError("precision must be a positive number")

    def subdivide(p0: complex, p1: complex, p2: complex, points: list):
        mid_curve = (p0 + 2 * p1 + p2) / 4
        mid_line = (p0 + p2) / 2

        if abs(mid_curve - mid_line) <= precision:
            points.append((p2.real, p2.imag))
            return

        p01 = (p0 + p1) / 2
        p12 = (p1 + p2) / 2
        p012 = (p01 + p12) / 2

        subdivide(p0, p01, p012, points)
        subdivide(p012, p12, p2, points)

    result = [(segment.start.real, segment.start.imag)]
    subdivide(segment.start, segment.control, segment.end, result)
    return result

def approx_cubic_bezier(segment: svgpathtools.CubicBezier, precision: float):
    if precision <= 0:
        raise ValueError("precision must be a positive number")

    def subdivide(p0: complex, p1: complex, p2: complex, p3: complex, points: list):
        mid_curve = (p0 + 3 * p1 + 3 * p2 + p3) / 8
        mid_line = (p0 + p3) / 2
        
        if abs(mid_curve - mid_line) <= precision:
            points.append((p3.real, p3.imag))
            return

        p01 = (p0 + p1) / 2
        p12 = (p1 + p2) / 2
        p23 = (p2 + p3) / 2
        p012 = (p01 + p12) / 2
        p123 = (p12 + p23) / 2
        p0123 = (p012 + p123) / 2

        subdivide(p0, p01, p012, p0123, points)
        subdivide(p0123, p123, p23, p3, points)

    result = [(segment.start.real, segment.start.imag)]
    subdivide(segment.start, segment.control1, segment.control2, segment.end, result)
    return result

def sort_paths(paths: list):
    output = []

    last_end = (0,0)
    for _ in tqdm(range(len(paths))):
        distances = [np.linalg.norm(np.array(p[0]) - np.array(last_end)) for p in paths]
        closest_index = np.argmin(distances)
        output.append(paths[closest_index])
        last_end = paths[closest_index][-1]
        paths.pop(closest_index)
    return output

def merge_paths(paths: list, threshold: float = 1.0):
    output = [paths[0]]
    for i in range(1, len(paths)):
        if np.linalg.norm(np.array(paths[i][0]) - np.array(paths[i-1][-1])) < threshold:
            output[-1] = output[-1] + paths[i]
        else:
            output.append(paths[i])
    return output

    
if __name__ == "__main__":
    paths = process_svg("./data/proc.svg", bounding_box=(-38, 273, 93, 303), precision=0.3)
    paths = sort_paths(paths)

    paths = merge_paths(paths, threshold=1.0)
    paths.append([(-40,94), (-40, 305),(275, 305),(275, 94),(-40, 94)])

    for p in paths:
        xs, ys= [], []
        for x, y in p:
            xs.append(x)
            ys.append(y)
        plt.plot(xs, ys, linewidth=1, color='black')
        # plt.scatter(xs[0], ys[0], color='green', s=5)
        # plt.scatter(xs[-1], ys[-1], color='red', s=5)

    trap_x, trap_y = [0, 235, 365, -130, 0], [0, 0, 305, 305, 0]
    plt.plot(trap_x, trap_y, linewidth=1.5, color='red', linestyle='--')


    print(len(paths))

    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
