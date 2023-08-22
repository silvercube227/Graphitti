# Created by : Alex Neary
# Created 08/2022


import matplotlib.pyplot as plt
import geopandas as gpd
import networkx as nx
import numpy as np
from shapely.ops import unary_union
from shapely.geometry import Polygon
import math


def main():
    # initialize graph
    G = nx.DiGraph()

    region_string = []  # stores the strings of squares that will be set as caller region attributes

    out_file_name = "King_county_NG911"

    square_counter = 0

    # read in GIS layer data
    psap_layer = gpd.read_file("GIS_data/Layers/PSAP_layer.gpkg")
    ems_layer = gpd.read_file("GIS_data/Layers/EMS_layer.gpkg")
    law_layer = gpd.read_file("GIS_data/Layers/Law_layer.gpkg")
    fire_layer = gpd.read_file("GIS_data/Layers/Fire_layer.gpkg")
    provisioning_layer = gpd.read_file("GIS_data/Layers/Provisioning_layer.gpkg")

    # create series of boolean values denoting whether geometry is within King County
    psap_within_kc = psap_layer.within(provisioning_layer.iloc[21].geometry)
    ems_within_kc = ems_layer.within(provisioning_layer.iloc[21].geometry)
    law_within_kc = law_layer.within(provisioning_layer.iloc[21].geometry)
    fire_within_kc = fire_layer.within(provisioning_layer.iloc[21].geometry)

    # create new GeoDataFrames of just items located within King County using series above
    kc_psap = psap_layer.drop(np.where(psap_within_kc == False)[0])
    kc_ems = ems_layer.drop(np.where(ems_within_kc == False)[0])
    kc_law = law_layer.drop(np.where(law_within_kc == False)[0])
    kc_fire = fire_layer.drop(np.where(fire_within_kc == False)[0])

    # area_multiplier gets multiplied by the smallest psap area to determine size of the squares in the grid
    area_multiplier = 10

    # Some of the data from the state had messed up psap names. This line fixes them so they can be consolidated
    kc_psap.loc[[265, 262, 185], 'DsplayName'] = "King County Sheriff's Office - Marine Patrol"

    names = [] # 2 empty lists for storing names and polygons for merging psaps together
    polys = []
    es_nguid = [] # list for storing the nguids

    # Loops through and finds all unique names, as well as sorting all the polygons that make up those regions
    for n in range(kc_psap.shape[0]):
        if (kc_psap.iloc[n].DsplayName) in names:
            polys[names.index(kc_psap.iloc[n].DsplayName)].append(kc_psap.iloc[n].geometry)
        else:
            names.append(kc_psap.iloc[n].DsplayName)
            polys.append([kc_psap.iloc[n].geometry])
            es_nguid.append(kc_psap.iloc[n].ES_NGUID)

    # Takes the lists of polygons, and merges them into new polygons for the creation of the merged_kc_psap GeoDataFrame
    merged_polys = []
    for m in range(len(polys)):
        merged_polys.append(unary_union(polys[m]))

    # Create a new GeoDataFrame with the unique names and merged geometries
    merged_kc_psap = gpd.GeoDataFrame({'DisplayName': names, 'geometry': merged_polys, 'ES_NGUID': es_nguid}, crs=kc_psap.crs)

    # Find the area of the smallest merged psap, use that to determine the square size
    areas = merged_kc_psap.area
    side_length = math.sqrt(areas.min() * area_multiplier)

    # Creates a grid of squares based on the bounds of merged_kc_psaps, and the side_length
    xmin, ymin, xmax, ymax = merged_kc_psap.total_bounds
    cols = list(np.arange(xmin, xmax + side_length, side_length))
    rows = list(np.arange(ymin, ymax + side_length, side_length))
    squares = []
    for x in cols[:-1]:
        for y in rows[:-1]:
            squares.append(
                Polygon([(x, y), (x + side_length, y), (x + side_length, y + side_length), (x, y + side_length)]))
    grid = gpd.GeoDataFrame({'geometry': squares}, crs=kc_psap.crs)

    # show resulting maps
    # merged_kc_psap.plot()
    # kc_ems.plot()
    # kc_psap.plot()
    # kc_law.plot()
    # kc_fire.plot()
    # plt.show()

    # Loop through all EMS boundaries, adding nodes and representative points
    for w in range(kc_ems.shape[0]):
        # Find a representative point for the boundary, and convert to string form
        pt = kc_ems.iloc[w].geometry.representative_point()
        rep_point = str(pt.x) + ", " + str(pt.y)

        G.add_node(kc_ems.iloc[w].ES_NGUID, objectID=kc_ems.iloc[w].ES_NGUID, name=kc_ems.iloc[w].DsplayName,
                   type="EMS", y=pt.y, x=pt.x)

    # Loop through all Law boundaries, adding nodes with representative points
    for v in range(kc_law.shape[0]):
        # Find a representative point for the boundary, and convert to string form
        pt = kc_law.iloc[v].geometry.representative_point()
        rep_point = str(pt.x) + ", " + str(pt.y)
        G.add_node(kc_law.iloc[v].ES_NGUID, objectID=kc_law.iloc[v].ES_NGUID, name=kc_law.iloc[v].DsplayName,
                   type="LAW",y=pt.y, x=pt.x)

    # Loop through all Fire boundaries, adding nodes with representative points
    for u in range(kc_fire.shape[0]):
        # Find a representative point for the boundary, and convert to string form
        pt = kc_fire.iloc[u].geometry.representative_point()
        rep_point = str(pt.x) + ", " + str(pt.y)
        G.add_node(kc_fire.iloc[u].ES_NGUID, objectID=kc_fire.iloc[u].ES_NGUID, name=kc_fire.iloc[u].DsplayName,
                   type="FIRE", y=pt.y, x=pt.x)

    # Loop through all PSAPs, adding each as nodes, and checking against all EMS, Fire, Law boundaries
    for x in range(merged_kc_psap.shape[0]):
        # add PSAP node to graph
        pt = kc_fire.iloc[x].geometry.representative_point()
        rep_point = str(pt.x) + ", " + str(pt.y)
        G.add_node(merged_kc_psap.iloc[x].ES_NGUID, objectID=merged_kc_psap.iloc[x].ES_NGUID,
                   name=merged_kc_psap.iloc[x].DisplayName, type="PSAP", y=pt.y,  x=pt.x)

        # find first
        # makes sure that every PSAP has at least 1 call region square
        pt = merged_kc_psap.iloc[x].geometry.representative_point()
        contain_mask = grid.contains(pt)
        first_square = grid.iloc[contain_mask[contain_mask].index].geometry
        bounds = first_square.bounds.values
        region_string.append("[(" + str(bounds[0][0]) + ", " + str(bounds[0][1]) + "), (" + str(bounds[0][2]) + ", " + str(bounds[0][3]) + ")]")
        square_counter += 1
        grid = grid.drop(contain_mask[contain_mask].index)

        # adding in all "adjacent PSAP" edges
        for y in range(merged_kc_psap.shape[0]):
            # finds all PSAPs that share a border with the current PSAP, and adds in adjacency edges
            if x != y and merged_kc_psap.iloc[x].geometry.touches(merged_kc_psap.iloc[y].geometry):
                G.add_edge(merged_kc_psap.iloc[x].ES_NGUID, merged_kc_psap.iloc[y].ES_NGUID)
                G.add_edge(merged_kc_psap.iloc[y].ES_NGUID, merged_kc_psap.iloc[x].ES_NGUID)

        # Loop through all EMS boundaries adding edges to relevant PSAP nodes
        for z in range(kc_ems.shape[0]):
            # Add edges between EMS and PSAP node for boundaries that overlap in any way
            if (kc_ems.iloc[z].geometry.intersects(merged_kc_psap.iloc[x].geometry) and not kc_ems.iloc[z].geometry.touches(
                    merged_kc_psap.iloc[x].geometry)) or kc_ems.iloc[z].geometry.within(merged_kc_psap.iloc[x].geometry):
                G.add_edge(merged_kc_psap.iloc[x].ES_NGUID, kc_ems.iloc[z].ES_NGUID)
                G.add_edge(kc_ems.iloc[z].ES_NGUID, merged_kc_psap.iloc[x].ES_NGUID)

        # Loop through all Law boundaries adding edges to relevant PSAP nodes
        for a in range(kc_law.shape[0]):
            # Add edges between Law and PSAP node for boundaries that overlap in any way
            if (kc_law.iloc[a].geometry.intersects(merged_kc_psap.iloc[x].geometry) and not kc_law.iloc[a].geometry.touches(
                    merged_kc_psap.iloc[x].geometry)) or kc_law.iloc[a].geometry.within(merged_kc_psap.iloc[x].geometry):
                G.add_edge(merged_kc_psap.iloc[x].ES_NGUID, kc_law.iloc[a].ES_NGUID)
                G.add_edge(kc_law.iloc[a].ES_NGUID, merged_kc_psap.iloc[x].ES_NGUID)

        # Loop through all Fire boundaries adding edges to relevant PSAP nodes
        for b in range(kc_fire.shape[0]):
            # Add edges between Fire and PSAP node for boundaries that overlap in any way
            if (kc_fire.iloc[b].geometry.intersects(merged_kc_psap.iloc[x].geometry) and not kc_fire.iloc[b].geometry.touches(
                    merged_kc_psap.iloc[x].geometry)) or kc_fire.iloc[b].geometry.within(merged_kc_psap.iloc[x].geometry):
                G.add_edge(merged_kc_psap.iloc[x].ES_NGUID, kc_fire.iloc[b].ES_NGUID)
                G.add_edge(kc_fire.iloc[b].ES_NGUID, merged_kc_psap.iloc[x].ES_NGUID)

    # Loop through all the squares in our grid, checking if each is completely within, or intersects with any psap
    # boundary
    for x in range(grid.shape[0]):
        # Finds the index of any psap that contains this square
        within_mask = merged_kc_psap.contains(grid.iloc[x].geometry)
        psap_index = within_mask[within_mask].index
        # If this square is completely contained inside a psap, add the coords to the appropriate region_string
        if psap_index.size != 0:
            sq = grid.iloc[x].geometry
            bounds = sq.bounds
            region_string[int(psap_index[0])] = region_string[int(psap_index[0])] + ", [(" + str(bounds[0]) + ", " + str(bounds[1]) + "), (" + str(bounds[2]) + ", " + str(bounds[3]) + ")]"
            square_counter += 1
            continue
        # If there is no psap that fully contains the square, find the area of all intersecting psaps, and assign
        # square to the psap with the largest overlap
        intersection_areas = []
        for y in range(merged_kc_psap.shape[0]):
            intersection_areas.append(grid.iloc[x].geometry.intersection(merged_kc_psap.iloc[y].geometry).area)
        if max(intersection_areas) > 0:
            sq = grid.iloc[x].geometry
            bounds = sq.bounds
            region_string[intersection_areas.index(max(intersection_areas))] = region_string[intersection_areas.index(max(intersection_areas))] + ", [(" + str(bounds[0]) + ", " + str(
                bounds[1]) + "), (" + str(bounds[2]) + ", " + str(bounds[3]) + ")]"
            square_counter += 1

    # Creates one caller region node for each psap, and sets the appropriate region_string as an attribute.
    for n in range(merged_kc_psap.shape[0]):
        region_name = str(merged_kc_psap.iloc[n].DisplayName) + " Caller region"
        caller_region_id = str(merged_kc_psap.iloc[n].ES_NGUID) + "_CR"
        G.add_node(caller_region_id, objectID=caller_region_id, name=region_name, type="CALR", segments=str(region_string[n]))
        G.add_edge(caller_region_id, str(merged_kc_psap.iloc[n].ES_NGUID))
        G.add_edge(str(merged_kc_psap.iloc[n].ES_NGUID), caller_region_id)

    # Print out graph information and produce .gexf file representing graph
    print("Number of nodes in graph:", G.number_of_nodes())
    print("Number of edges in graph:", G.number_of_edges())
    print("Number of square in grid: ", square_counter)
    # We will made the vertex ids consecutive set of integers starting at zero.
    # This is what happens when loaded into a Boost Graph Library graph and we will
    # have a direct map between vertex ids.
    G = nx.convert_node_labels_to_integers(G, first_label=0, ordering='default')
    nx.write_gexf(G, "graph_files/" + out_file_name + ".gexf")
    nx.write_graphml(G, "graph_files/" + out_file_name + ".graphml", named_key_ids=True)
if __name__ == '__main__':
    main()
