import networkx as nx
from PIL import Image, ImageDraw
import xml.etree.ElementTree as ET

# Load GraphML data
tree = ET.parse('graph_files/King_county_NG911.graphml')
root = tree.getroot()
#initialize graph
G = nx.Graph()

# Type attribute key
type_attribute_key = 'type'
# Namespace from root
nsmap = {'xmlns': 'http://graphml.graphdrawing.org/xmlns'}
for node in root.findall('.//{http://graphml.graphdrawing.org/xmlns}node'):
    type_element = node.find(f'.//{{{nsmap["xmlns"]}}}data[@key="{type_attribute_key}"]')
    if type_element is not None and type_element.text == 'CALR':
        node_id = node.get('id')
        G.add_node(node_id)

# Choose and run a layout algorithm (e.g., spring layout)
pos = nx.spring_layout(G)

# Calculate cartogram distortions (if applicable)
# Apply distortions to the layout

# Define image dimensions
img_width = 800  # Adjust as needed
img_height = 600  # Adjust as needed

# Generate the cartogram image
image = Image.new('RGB', (img_width, img_height), 'white')
draw = ImageDraw.Draw(image)

# Iterate through nodes and draw pixels
for node in pos.items():
    print(node)
    segments_data = node.find(f'.//{{{nsmap["xmlns"]}}}data[@key="segments"]')
    print(segments_data)
    segments = eval(G.nodes[node][''])  # Convert string to list

    # Determine color based on node data (customize as needed)
    color = (0, 0, 0)  # Default color

    # Draw pixels for each segment
    for segment in segments:
        for coord in segment:
            x0 = int(coord[0] * img_width)
            y0 = int(coord[1] * img_height)
            x1 = x0 + 1  # Use 1 pixel for grid cells
            y1 = y0 + 1  # Use 1 pixel for grid cells
            draw.rectangle([x0, y0, x1, y1], fill=color)

# Save the image
image.save('cartogram.png')
