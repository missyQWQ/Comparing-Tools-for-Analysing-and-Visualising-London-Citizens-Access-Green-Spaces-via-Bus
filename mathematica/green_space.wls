
breakdown = {};
DiffUnix = Round[AbsoluteTime[] - UnixTime[], 100];
ut = ut = (# - DiffUnix &)@*AbsoluteTime;

busStopPath = "./data/bus-stops.csv";
busSequencePath = "./data/bus-sequences.csv";
londonPath = "./data/londonUTLA_full.csv";
populationPath = 
  "./data/LSOA_(Dec_2011)_Population_Weighted_Centroids_in_England_and_Wales.csv";
greenSpacePath = "./data/green_space.csv";

BUS\[LetterSpace]SPEED = 4.;
WALKING\[LetterSpace]SPEED = 1.;


(* Data Import *)
breakdown = Append[breakdown, ut[]];
busStop = 
  Import[busStopPath, "Dataset", HeaderLines -> 1][
   All, {"Stop_Code_LBSL", "Location_Easting", "Location_Northing"}];
routes = Import[busSequencePath, "Dataset", HeaderLines -> 1][
   All, {"Route", "Run", "Sequence", "Stop_Code_LBSL", 
    "Location_Easting", "Location_Northing"}];
councils = Import[londonPath, "Dataset", HeaderLines -> 1];
population = Import[populationPath, "Dataset", HeaderLines -> 1];
greenSpace = Import[greenSpacePath, "Dataset", HeaderLines -> 1];

(* Preprocess *)
breakdown = Append[breakdown, ut[]];
busStop = 
  busStop[All, <|"id" -> "Stop_Code_LBSL", "x" -> "Location_Easting", 
    "y" -> "Location_Northing"|>];
routes = routes[
   All, <|"id" -> "Route", "run" -> "Run", "seq" -> "Sequence", 
    "stop" -> "Stop_Code_LBSL", "x" -> "Location_Easting", 
    "y" -> "Location_Northing"|>];
councils = Union[Normal@councils[SortBy[#LAName &], "LAName"]];
population = 
  population[
   All, <|"x" -> "X", "y" -> "Y", "oid" -> "OBJECTID", 
    "lsoa" -> "lsoa11cd", "council" -> "lsoa11nm", 
    "gid" -> "GlobalID"|>];
population = 
  population[All, {"council" -> (StringTake[#, {1, -6}] &)}];
population = population[Select[MemberQ[councils, #council] &]];
lsoaLst = Union[Normal@population[All, "lsoa"]];
greenSpace = greenSpace[Select[MemberQ[lsoaLst, #LSOACode] &], All];
busStopPos = 
  Association@
   MapThread[#1 -> {#2, #3} &, 
    Normal /@ {busStop[All, "id"], busStop[All, "x"], 
      busStop[All, "y"]}];
populationPos = 
  Association@
   MapThread[#1 -> {#2, #3} &, 
    Normal /@ {population[All, "lsoa"], population[All, "x"], 
      population[All, "y"]}];
pos = Join[busStopPos, populationPos];

(* Building Graph *)
breakdown = Append[breakdown, ut[]];
nearest = 
  ParallelMap[
   Nearest[Normal@busStop[All, {"x", "y"}][Values] -> {"Index", 
       "Distance"}, #, 5] &, 
   Normal@population[All, {"x", "y"}][Values]];
nearestStops = nearest[[All, All, 1]];
stopDistance = nearest[[All, All, 2]];
routesGrouped = Normal@routes[GroupBy["id"], GroupBy["run"]];
busGraphData = 
  Module[{stopPos, x, y, stops}, 
     ParallelTable[{stops, x, y} = 
       Table[#[tag] & /@ Flatten@data, {tag, {"stop", "x", "y"}}]; 
      stopPos = MapThread[{#1, #2} &, {x, y}]; 
      MapThread[#1 \[DirectedEdge] #2 -> 
         Norm[#3 - #4]/BUS\[LetterSpace]SPEED &, {stops[[;; -2]], 
        stops[[2 ;;]], stopPos[[;; -2]], stopPos[[2 ;;]]}], {i, 
       Length@routesGrouped}, {data, routesGrouped[[i]]}]] // 
    Flatten // Union;
populationZipped = 
  MapThread[{#1, #2, #3} &, {Normal@population[All, "lsoa"], 
    nearestStops, stopDistance}];
populationGraphData = 
  Table[MapThread[{data[[
           1]] \[DirectedEdge] #1 -> #2, #1 \[DirectedEdge] 
          data[[1]] -> #2} &, {Normal@busStop[data[[2]], "id"], 
       data[[3]]/WALKING\[LetterSpace]SPEED}], {data, 
      populationZipped}] // Flatten // Union;
graphData = busGraphData~Join~populationGraphData // Union;
edges = #[[1]] & /@ graphData;
weights = #[[2]] & /@ graphData;
G = Graph[edges, EdgeWeight -> weights];

(* Calculation *)
breakdown = Append[breakdown, ut[]];
largeGreenSpace = 
  Union@Normal@greenSpace[Select[#GSDIAvgArea == 4 &], "LSOACode"];
largeGreenSpace = Intersection[largeGreenSpace, VertexList[G]];
reachability = 
  Module[{disToGreen, v, nbg}, 
   ParallelTable[v = row["LSOACode"]; 
    nbg = NeighborhoodGraph[G, v, 18];
    disToGreen = 
     GraphDistance[nbg, v, #, Method -> "Dijkstra"] & /@ 
      Intersection[VertexList[nbg], largeGreenSpace]; 
    v -> Piecewise[{{300 row["Pcnt_PopArea_With_GOSpace_Access"] + 
         Sqrt@row["Area"], 
        row["GSDIAvgArea"] > 2 || row["GSDI_Access"] > 2}, {Infinity, 
        Length@disToGreen == 0}}, Min@disToGreen], {row, 
     Normal@greenSpace}]];

(* Visualization *)
breakdown = Append[breakdown, ut[]];
hist = Histogram[{None, Flatten@Values@reachability}, 100, 
   AxesLabel -> {"Time to reach large green space (\!\(\*
StyleBox[\"s\",\nFontSlant->\"Italic\"]\))", 
     "Population point count"}, ImageSize -> Full];
Export["hist.png", hist, ImageResolution -> 300];


Module[{nodes, m, hotSpotSize, pointStyles, hotspot}, nodes = lsoaLst;
  m = Max[Flatten@Values@reachability] + 10;
  hotSpotSize = 
   Piecewise[{{.1, # == Infinity}, {(m - #)/3000, # != Infinity}}] & /@
     Table[Lookup[reachability, lsoa, Infinity], {lsoa, nodes}];
  pointStyles = 
   Table[{Darker@Green, PointSize[hotSpotSize[[i]]/1200], 
     Point[pos[nodes[[i]]]]}, {i, Length@nodes}];
  hotspot = Graphics[pointStyles, ImageSize -> Large];
  Export["hotspot.png", hotspot, ImageResolution -> 300];
  ];

AbsoluteTiming@
 Module[ {nodes, nodeCoord, Gpos, populationByCouncil, councilGraphs, 
   imageBusStops, imageBusSequences, imagesCouncilsList, 
   graphsToPlot, colorful},
  nodes = Normal@busStop[All, "id"];
  nodeCoord = pos[#] &;
  Gpos = Graph[edges, VertexCoordinates -> nodeCoord /@ VertexList[G]];
  populationByCouncil = population[GroupBy["council"]];
  councilGraphs = 
   Module[{data}, Table[data = Normal@populationByCouncil[council];
     Subgraph[Gpos, #["lsoa"] & /@ data], {council, councils}]];
  
  imageBusStops = 
   Legended[
    GraphPlot[Subgraph[Gpos, nodes], EdgeShapeFunction -> None, 
     BaseStyle -> EdgeForm[None], VertexSize -> .2, 
     VertexStyle -> LightGray, ImageSize -> Full], 
    SwatchLegend[{LightGray}, {"Bus Stops"}]];
  imageBusSequences = 
   Legended[
    GraphPlot[Gpos, EdgeStyle -> LightGray, 
     VertexShapeFunction -> None, DirectedEdges -> False, 
     ImageSize -> Full], SwatchLegend[{LightGray}, {"Bus Routes"}]];
  imagesCouncilsList = 
   Table[Legended[
     GraphPlot[councilGraphs[[i]], EdgeShapeFunction -> None, 
      BaseStyle -> EdgeForm[None], VertexSize -> .8, 
      VertexStyle -> ColorData[54][i], ImageSize -> Full], 
     SwatchLegend[{ColorData[54][i]}, {councils[[i]]}]], {i, 
     Length@councils}];
  
  graphsToPlot = 
   Join[{imageBusStops, imageBusSequences}, imagesCouncilsList];
  colorful = Show[graphsToPlot, ImageSize -> Full];
  Export["graph.png", colorful];
  ]

  Export["breakdown.json", breakdown, "JSON"]
