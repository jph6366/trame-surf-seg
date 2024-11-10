import math
from collections import defaultdict
from vtk import (
    vtkTriangle,
    vtkPolyData,
    vtkPointData,
    vtkUnsignedCharArray,
    vtkCellArray,
    vtkCellArray,
    vtkPoints,
    # vtkNew, 
    # replace with:  auto actor = vtkSmartPointer::New();
    vtkKdTree,
    vtkDataSetCollection
)

from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkProperty,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

import vtk


# ---------------------------------------------------------
# Triangle class
# ---------------------------------------------------------

class Vertex:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __sub__(self, other):
        return Vertex(self.x - other.x, self.y - other.y, self.z - other.z)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def distance_to(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

class Triangle:
    def __init__(self, v1, v2, v3):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    def shares_vertex_with(self, other, radius=0.0025):
        def is_within_radius(v1, v2):
            return (v1 - v2).length() <= radius

        return (
            self.v1 == other.v1 or self.v1 == other.v2 or self.v1 == other.v3 or
            is_within_radius(self.v1, other.v1) or is_within_radius(self.v1, other.v2) or is_within_radius(self.v1, other.v3) or
            self.v2 == other.v1 or self.v2 == other.v2 or self.v2 == other.v3 or
            is_within_radius(self.v2, other.v1) or is_within_radius(self.v2, other.v2) or is_within_radius(self.v2, other.v3) or
            self.v3 == other.v1 or self.v3 == other.v2 or self.v3 == other.v3 or
            is_within_radius(self.v3, other.v1) or is_within_radius(self.v3, other.v2) or is_within_radius(self.v3, other.v3)
        )

    def get_normal(self):
        u = Vertex(self.v2.x - self.v1.x, self.v2.y - self.v1.y, self.v2.z - self.v1.z)
        v = Vertex(self.v3.x - self.v1.x, self.v3.y - self.v1.y, self.v3.z - self.v1.z)
        return Vertex(
            u.y * v.z - u.z * v.y,
            u.z * v.x - u.x * v.z,
            u.x * v.y - u.y * v.x
        )

# ---------------------------------------------------------
# Union-Find(Disjoint-set) Forest class
# ---------------------------------------------------------


class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def unite(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x != root_y:
            if self.rank[root_x] > self.rank[root_y]:
                self.parent[root_y] = root_x
            elif self.rank[root_x] < self.rank[root_y]:
                self.parent[root_x] = root_y
            else:
                self.parent[root_y] = root_x
                self.rank[root_x] += 1

    def get_all_in_same_set(self, element):
        root = self.find(element)
        same_set = [key for key in self.parent if self.find(key) == root]
        return same_set

    def get_all_not_in_same_set(self, element):
        root = self.find(element)
        not_same_set = [key for key in self.parent if self.find(key) != root]
        return not_same_set
    
# ---------------------------------------------------------
# Surface Segmentation Helper Methods
# ---------------------------------------------------------


def read_vertices(filename):
    try:
        vertices = []
        with open(filename, 'r') as fin:
            for line in fin:
                values = [float(value) for value in line.strip().split(',')]
                if len(values) == 9:
                    v0 = Vertex(values[0], values[1], values[2])
                    v1 = Vertex(values[3], values[4], values[5])
                    v2 = Vertex(values[6], values[7], values[8])
                    vertices.append(Triangle(v0, v1, v2))
                else:
                    print(f"Invalid line format: {line}")
        return vertices
    except FileNotFoundError:
        print("Failed to open file.")

def construct_adjacency(triangles):
    adjacency_list = defaultdict(set)
    for i in range(len(triangles)):
        for j in range(i + 1, len(triangles)):
            if triangles[i].shares_vertex_with(triangles[j]):
                adjacency_list[i].add(j)
                adjacency_list[j].add(i)
    return adjacency_list

def build_forest(triangles, adjacency):
    uf = UnionFind()
    for i in range(len(triangles)):
        uf.add(i)
    for index, neighbors in adjacency.items():
        for idx in neighbors:
            uf.unite(index, idx)
    return uf

def count_spanning_trees(triangles, forest):
    st = {}
    for i in range(len(triangles)):
        root = forest.find(i)
        if root not in st:
            st[root] = 0
        st[root] += 3
    return st


# ---------------------------------------------------------
# Surface Segmentation class
# ---------------------------------------------------------


class SurfSeg:
    def __init__(self, vertices):
        self.triangles = read_vertices(vertices)
        self.adjacency = construct_adjacency(self.triangles)
        self.forest = build_forest(self.triangles, self.adjacency)
        self.spanning_trees = count_spanning_trees(self.triangles, self.forest)
        
        self.points = vtkPoints()
        self.colors = vtkUnsignedCharArray()
        self.colors.SetNumberOfComponents(3)
        self.colors.SetName("Colors")
        self.surfaces = vtkCellArray()

        for index, count in self.spanning_trees.items():
            neighborPoints = self._initialize_space(self.triangles, self.forest, index)
            self._nearest_neighbor_color_map(self.points, self.colors, neighborPoints, self.triangles, self.forest, index)

        for i in range(len(self.triangles)):
            triangle = vtkTriangle()
            triangle.GetPointIds().SetId(0, i*3)
            triangle.GetPointIds().SetId(1, i*3 + 1)
            triangle.GetPointIds().SetId(2, i*3 + 2)
            self.surfaces.InsertNextCell(triangle)

        self._render_surf(self.points, self.surfaces, self.colors)

        


    def _initialize_space(self, triangles, forest, surf):
        diff_set = forest.get_all_not_in_same_set(surf)
        points = vtkPoints()
        for j in diff_set:
            tri = triangles[j]
            x = [tri.v1.x, tri.v1.y, tri.v1.z]
            y = [tri.v2.x, tri.v2.y, tri.v2.z]
            z = [tri.v3.x, tri.v3.y, tri.v3.z]
            points.InsertNextPoint(x)
            points.InsertNextPoint(y)
            points.InsertNextPoint(z)
        return points

    def _nearest_neighbor_color_map(self, points, colors, points_n, triangles, uf, surface):


        kDTree = vtk.vtkKdTree()
        kDTree.BuildLocatorFromPoints(points_n)

        # Print the number of points in each unique surface
        print(f"Surface {surface}")
        same_set = uf.get_all_in_same_set(surface)
        print(len(same_set))

        NNDist = vtk.reference(0.0) # create a proxy to a Python float object
        for j in same_set:
            tri = triangles[j]
            
            # Points from the triangle
            x = [tri.v1.x, tri.v1.y, tri.v1.z]
            y = [tri.v2.x, tri.v2.y, tri.v2.z]
            z = [tri.v3.x, tri.v3.y, tri.v3.z]

            # Insert points and calculate nearest neighbor distance for each
            points.InsertNextPoint(x)
            
            NNId =kDTree.FindClosestPoint(x, NNDist)
            print(NNDist)
            if NNDist > 0.0:
                r = int(255 / (1 + math.exp(-0.1 * (NNDist - 100))))
            else:
                r = 0.0
            b = 255 - r
            colors.InsertNextTuple3(r, 0.0, b)

            points.InsertNextPoint(y)
            NNId =kDTree.FindClosestPoint(x, NNDist)
            if NNDist > 0.0:
                r = int(255 / (1 + math.exp(-0.1 * (NNDist - 100))))
            else:
                r = 0.0
            b = 255 - r
            colors.InsertNextTuple3(r, 0.0, b)

            points.InsertNextPoint(z)
            NNId =kDTree.FindClosestPoint(x, NNDist)
            if NNDist > 0.0:
                r = int(255 / (1 + math.exp(-0.1 * (NNDist - 100))))
            else:
                r = 0.0
            b = 255 - r
            colors.InsertNextTuple3(r, 0.0, b)
            
    def _render_surf(self, points, surfaces, colors):
        # Create surface polydata
        surface_poly_data = vtkPolyData()
        surface_poly_data.SetPoints(points)
        surface_poly_data.SetPolys(surfaces)
        surface_poly_data.GetPointData().SetScalars(colors)

        # Create a mapper
        surface_mapper = vtkPolyDataMapper()
        surface_mapper.SetInputData(surface_poly_data)

        # Create an actor
        surface_actor = vtkActor()
        surface_actor.SetMapper(surface_mapper)

        # Set up Phong lighting model for the surface
        surface_actor.GetProperty().SetInterpolationToPhong()
        surface_actor.GetProperty().SetDiffuse(0.8)
        surface_actor.GetProperty().SetSpecular(0.5)
        surface_actor.GetProperty().SetSpecularPower(30.0)

        # Create renderer, render window, and interactor
        surface_renderer = vtkRenderer()
        self.surface_render_window = vtkRenderWindow()
        self.surface_render_window.AddRenderer(surface_renderer)

        surface_render_window_interactor = vtkRenderWindowInteractor()
        surface_render_window_interactor.SetRenderWindow(self.surface_render_window)

        # Add actor to renderer
        surface_renderer.AddActor(surface_actor)
        surface_renderer.SetBackground(0.1, 0.2, 0.3)

        # Render and start interaction
        self.surface_render_window.Render()
        # surface_render_window_interactor.Start()