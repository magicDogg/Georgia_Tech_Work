# -*- coding: utf-8 -*-
"""
    mst.py       Intro to Graduate Algorithms
    
    Union find object for kruskal algorithm using adjacency matrix
    Also known as a Disjoint-set data structure
    See the text (Dasgupta)
"""

import argparse
import GA_ProjectUtils as util

class unionFind:
    def __init__(self, n):
        self.pi = [i for i in range(n)]
        self.rank = [0 for i in range(n)]

    def areConnected(self, p, q):
        """
            return true if 2 nodes are connected or false if they are
            not by comparing their roots
        """
        #TODO Your Code Goes Here
        return (self.pi[p] == q) or (self.pi[q] == p)

    def union(self, u, v):
        """
            build union of 2 components
            Be sure to maintain self.rank as needed to
            make sure your algorithm is optimal.
        """
        r_x = self.find(u)
        r_y = self.find(v)

        if r_x == r_y:
            return

        if self.rank[r_x] > self.rank[r_y]:
            self.pi[r_y] = r_x
        else:
            self.pi[r_x] = r_y
            if self.rank[r_x] == self.rank[r_y]:
                self.rank[r_y] = self.rank[r_y] + 1

    def find(self, p):
        """
            find the root of the set containing the
            passed vertex p - Must use path compression!
        """
        while p != self.pi[p]:
            p = self.pi[p]

        return p

def kruskal(G):
    """
        Kruskal algorithm
        G : graph object
    """
    #Build unionFind Object
    uf = unionFind(G.numVerts)
    #Make MST as a set
    MST = set()    
    #Get list of edges sorted by increasing weight
    sortedEdges = G.sortedEdges()   
    #Go through edges in sorted order smallest, to largest
    for e in sortedEdges:
        u, v = e

        if uf.find(u) != uf.find(v):
            # use the following line to add an edge to the MST.
            # You may change it's indentation/scope within the for loop
            MST.add(util.buildMSTEdge(G,e))
            uf.union(u, v)

        #TODOne - do not modify any other code below this line
    return MST, uf

def main():
    """
    main
    """
    #DO NOT REMOVE ANY ARGUMENTS FROM THE ARGPARSER BELOW
    parser = argparse.ArgumentParser(description='Minimum Spanning Tree Coding Quiz')
    #use this flag, or change the default here to use different graph description files
    parser.add_argument('-g', '--graphFile',  help='File holding graph data in specified format', default='small.txt', dest='graphDataFileName')
    #use this flag to print the graph and resulting MST
    parser.add_argument('-p', '--print', help='Print the MSTs?', default=False, dest='printMST')

    #args for autograder, DO NOT MODIFY ANY OF THESE
    parser.add_argument('-n', '--sName',  help='Student name, used for autograder', default='GT', dest='studentName')	
    parser.add_argument('-a', '--autograde',  help='Autograder-called (2) or not (1=default)', type=int, choices=[1, 2], default=1, dest='autograde')	
    args = parser.parse_args()
    
    #DO NOT MODIFY ANY OF THE FOLLOWING CODE
    #Build graph object
    graph = util.build_MSTBaseGraph(args)
    #you may print the configuration of the graph -- only effective for graphs with up to 10 vertex
    #graph.printMe()

    #Calculate kruskal's alg for MST
    MST_Kruskal, uf = kruskal(graph)
        
    #verify against provided prim's algorithm results
    util.verify_MSTKruskalResults(args, MST_Kruskal, args.printMST)
    
if __name__ == '__main__':
    main()