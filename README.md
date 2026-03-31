Given a simple polygon P , compute an “optimal” triangulation using dynamic programming. Here,
“optimal” may mean (a) minimum weight triangulation (minimize the sum of the edge lengths of
diagonals), (b) minimize the longest edge, (c) maximize the shortest edge, etc. The input is assumed
to be a text file whose first line gives the x and y coordinates of p (separated by a space), and whose
remaining lines give a clockwise listing of the (x, y) coordinates (floating point) of the vertices (two
floating point numbers, separated by a space). It will be useful to have the option of mouse-clicking
(and saving) input too. You may assume that the polygon is definitely simple.
Experimentally compare the weight of the resulting triangulation with the weight of the triangulation
obtained using ear clipping (algorithm Triangulate, from O’Rourke).