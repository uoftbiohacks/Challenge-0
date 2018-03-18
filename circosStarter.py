import svgwrite
from setUpCh import chSetUp
from math import cos, sin, pi

CENTER = (300,300)      #where to center our circos plot
RADIUS = 150            #size of circos plot
START = (0, RADIUS)     #for calculating gene arcs
CHROMLEN = 64444167     #nts on chromosome 20

#gene location and GOA based print - circos
#draw the chromosome as a circle and add arcs to represent gene occupancy
#add edges between genes that share the same GOA

def calcArcCoords(chDF):
    #calculate where each gene reaches on circos graph

    #each gene arc on the circular chromosome is some percentage of the total circle. Multiply this by 2pi to get
    #the theta corresponding to this arc. From an arbitraty start point (globally specified) we can add theta and
    #get the start, mid, and end points of the gene on the circle.

    #each gene will move from START by a rotation of theta. Use the rotation matrix to find new coordinates
    #(cos(theta)*START_x + sin(theta)*START_y, -sin(theta)*START_x+ cos(theta)*START_y)
    #where theta is the angle from START to the arc in radians

    #find the coordinates of the start of the arc
    chDF["thetaStart"] = (chDF.start/CHROMLEN)*(2*pi)
    chDF["arcStartX"] = chDF.thetaStart.apply(cos) * START[0] - chDF.thetaStart.apply(sin) * START[1]
    chDF["arcStartY"] = chDF.thetaStart.apply(sin) * START[0] + chDF.thetaStart.apply(cos) * START[1]

    #find the coordinates of the end of the arc
    chDF["thetaEnd"] = (chDF.end/CHROMLEN)*(2*pi)
    chDF["arcEndX"] = chDF.thetaEnd.apply(cos) * START[0] - chDF.thetaEnd.apply(sin) * START[1]
    chDF["arcEndY"] = chDF.thetaEnd.apply(sin) * START[0] + chDF.thetaEnd.apply(cos) * START[1]

    #find the coordinates of the middle of the arc(for edges to originate from)
    chDF["thetaMid"] = ((chDF.start+((chDF.end-chDF.start)/2))/CHROMLEN)*(2*pi)
    chDF["arcMidX"] = chDF.thetaMid.apply(cos) * START[0] - chDF.thetaMid.apply(sin) * START[1]
    chDF["arcMidY"] = chDF.thetaMid.apply(sin) * START[0] + chDF.thetaMid.apply(cos) * START[1]

    #now shift all coordinates to the defined center
    chDF.arcStartX = chDF.arcStartX + CENTER[0]
    chDF.arcStartY = chDF.arcStartY + CENTER[1]
    chDF.arcEndX = chDF.arcEndX + CENTER[0]
    chDF.arcEndY = chDF.arcEndY + CENTER[1]
    chDF.arcMidX = chDF.arcMidX + CENTER[0]
    chDF.arcMidY = chDF.arcMidY + CENTER[1]

    return chDF

def makeEdgeList(chDF):
    #return a list of edges between genes that have the same GOA, and the colour the edge should be drawn with

    edgeList = []

    for g in chDF.index:
        thisGOAid = chDF.loc[g].GOAid               #get the GOAid
        sharedGOA = chDF[chDF.GOAid == thisGOAid]   #get all other rows with same GOAid
        sharedGOA = sharedGOA.drop(g)               #remove self edges
        for f in sharedGOA.index:
            edgeList.append(((chDF.loc[g].arcMidX, chDF.loc[g].arcMidY),
                             (chDF.loc[f].arcMidX, chDF.loc[f].arcMidY),
                             chDF.loc[g].colour))

    return edgeList


def circoGeneDraw(chDF, chEdges, fName):

    dwg = svgwrite.Drawing(filename=fName)

    #add title
    dwg.add(dwg.text("CHR 20", insert=CENTER, fill="black", text_anchor="middle"))

    #draw chromosome line
    # dwg.add(dwg.circle(CENTER, RADIUS, fill_opacity=0.0, stroke="black", stroke_width=1))

    dwg.add(dwg.circle(CENTER, RADIUS, fill_opacity=0.0, stroke="black", stroke_width=1))
    from_ = "0 " + str(CENTER[0]) + " " + str(CENTER[1])
    to_ = "360 " + str(CENTER[0]) + " " + str(CENTER[1])
    # circle.add(
    #     dwg.animateTransform("rotate", "transform", id="circle", from_=from_, to=to_, dur="10s",
    #                            begin="0s", repeatCount="indefinite"))

    #draw edge for each shared GOA
    GOAedges = dwg.add(dwg.g(id="GOAedges", stroke_width=0.05))
    GOAedges.add(
        dwg.animateTransform("rotate", "transform", id="edges", from_=from_, to=to_, dur="36s",
                             begin="0s", repeatCount="indefinite"))

    for e in chEdges:
        eStart = e[0]
        eEnd = e[1]
        eCol = e[2]
        line = GOAedges.add(dwg.line(eStart, eEnd, stroke=eCol))
        # begin = "0s"
        # line.add(
        #     dwg.animateColor("fill", fill="remove", id="fills", begin="0s", end="2s"))

    #draw arcs for each gene
    geneArcs = dwg.add(dwg.g(id="geneArcs", fill="white", stroke_width=5))
    geneArcs.add(
        dwg.animateTransform("rotate", "transform", id="arcs", from_=from_, to=to_, dur="36s",
                             begin="0s", repeatCount="indefinite"))
    for g in chDF.index:
        #look up the gene arc start and end points and plug into drawing
        gStart = "M" + str(chDF.loc[g].arcStartX) + "," + str(chDF.loc[g].arcStartY)
        gArc = "A" + str(RADIUS) + "," + str(RADIUS)
        gEnd = str(chDF.loc[g].arcEndX) + "," + str(chDF.loc[g].arcEndY)
        geneArcs.add(dwg.path(d = gStart + gArc + " 0 0,1 " + gEnd, stroke=chDF.loc[g].colour))

    dwg.save()


if __name__ == '__main__':
    print("setting up...")
    ch20 = chSetUp()
    print("set up complete\ncomputing gene arcs...")
    ch20 = calcArcCoords(ch20)
    print("gene arcs computed\ncomputing edges... (this may take a few seconds)")
    ch20Edges = makeEdgeList(ch20)
    print("edges computed\nrendering svg... (this may take a few seconds)")
    circoGeneDraw(ch20, ch20Edges, "circosDraw.svg")

