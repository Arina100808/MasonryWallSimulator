from matplotlib import pyplot as plt

def get_extended_colors(n):
    colormaps = ['Set2', 'Dark2', 'Set3', 'Set1', 'Accent',
                 'Pastel1', 'tab20', 'Pastel2']
    colors = []

    for cmap_name in colormaps:
        cmap = plt.get_cmap(cmap_name)
        for i in range(cmap.N):
            colors.append(cmap(i))
            if len(colors) >= n:
                return colors
    return colors[:n]

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgb[0] * 255),
        int(rgb[1] * 255),
        int(rgb[2] * 255))
