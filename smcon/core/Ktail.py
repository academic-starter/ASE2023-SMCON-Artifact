"""
 * Implements the KTails algorithm as defined in Biermann & Feldman '72.
"""

import copy
import json
from visual_automata.fa.nfa import VisualNFA  
import argparse 

class Node:
    def __init__(self) -> None:
        self.parents = []
        self.children = []

    def addParent(self, node):
        if node not in self.parents:
            self.parents.append(node)

    def addChild(self, node):
        if node not in self.children:
            self.children.append(node)

    @property
    def unique_id(self):
        return self.__hash__()

class Graph:
    def __init__(self) -> None:
        self.root = Node()
        self.nodes = []
        self.transitions = dict() 
        self.nodes.append(self.root)

    def addNode(self, node):
        assert isinstance(node, Node)
        if node not in self.nodes:
            self.nodes.append(node)

    def removeNode(self, node: Node):
        
        if node.unique_id in self.transitions:
            del self.transitions[node.unique_id]
        
        for fromNodeIndex in copy.copy(self.transitions):
            for label in copy.copy(self.transitions[fromNodeIndex]):
                if self.transitions[fromNodeIndex][label] == node.unique_id:
                    # del self.transitions[fromNodeIndex][label]
                    self.transitions[fromNodeIndex].pop(label, None)
            if len(self.transitions[fromNodeIndex]) == 0:
                # del self.transitions[fromNodeIndex]
                self.transitions.pop(fromNodeIndex, None)

        for parent in copy.copy(node.parents):
            if node in parent.children:
                parent.children.remove(node)
            if node in node.parents:
                node.parents.remove(parent)

        for child in copy.copy(node.children):
            if node in child.parents:
                child.parents.remove(node)
            if child in node.children:
                node.children.remove(child)

        if node in self.nodes:
            self.nodes.remove(node)

    def hasNode(self, node):
        return node in self.nodes
    
    def hasTransition(self, node, label):
        if node not in self.nodes:
            return False 
        nodeIndex = node.unique_id
        if nodeIndex not in self.transitions:
            return False 
        return label in self.transitions[nodeIndex]

    def addTransition(self, fromNode, label, toNode):
        if label is None:
            return 
        if fromNode not in self.nodes:
            self.addNode(fromNode)
        if toNode not in self.nodes:
            self.addNode(toNode)
        if fromNode.unique_id not in self.transitions:
            self.transitions[fromNode.unique_id] = dict()
        self.transitions[fromNode.unique_id][label] = toNode.unique_id
        
        fromNode.addChild(toNode)
        toNode.addParent(fromNode)
    
    def getTransitionLabel(self, fromNode, toNode):
        assert fromNode in self.nodes
        for label in self.transitions[fromNode.unique_id]:
            assert toNode in self.nodes, "toNode not in nodes {}".format(toNode.unique_id)
            if self.transitions[fromNode.unique_id][label] == toNode.unique_id:
                return label
        return None
    
    def merge(self, node1, node2):
        node = Node()
        for parent in node1.parents:
            if parent == node1:
                self.addTransition(node, self.getTransitionLabel(parent, node1), node)
            else:
                self.addTransition(parent, self.getTransitionLabel(parent, node1), node)
         
        for parent in node2.parents:
            if parent == node2:
                self.addTransition(node, self.getTransitionLabel(parent, node2), node)
            else:
                self.addTransition(parent, self.getTransitionLabel(parent, node2), node)
            
        for child in node1.children:
            if child == node:
                self.addTransition(node, self.getTransitionLabel(node1, child), node)
            else:
                self.addTransition(node, self.getTransitionLabel(node1, child), child)
            
        for child in node2.children:
            if child == node2:
                self.addTransition(node, self.getTransitionLabel(node2, child), node)
            else:
                self.addTransition(node, self.getTransitionLabel(node2, child), child)
         
        self.removeNode(node1)
        self.removeNode(node2)
        self.addNode(node)
        self.removeDetachedNode()
    
    def removeDetachedNode(self):
        for node in copy.copy(self.nodes):
            if node != self.root and node.parents == []:
                self.removeNode(node)
                self.removeDetachedNode()
                return
        return 
    
    def isConnect(self, curNode, targetNode, visited = []):
        if curNode == targetNode:
            return True
        if curNode.unique_id not in self.transitions:
            return False
        if (curNode.unique_id, targetNode.unique_id) in visited:
            return False
        visited.append((curNode.unique_id, targetNode.unique_id))

        for label in self.transitions[curNode.unique_id]:
            nextNodeIndex = self.transitions[curNode.unique_id][label]
            nextNode = list(filter(lambda node: node.unique_id == nextNodeIndex, self.nodes))[0]
            if self.isConnect(nextNode, targetNode, visited = visited):
                return True
        return False

class PrefixTree:
    def __init__(self) -> None:
        self.graph = Graph()
        
    def add(self, trace):
        root = self.graph.root
        for word in trace:
            if not self.graph.hasTransition(root, word):
                node = Node()
                self.graph.addTransition(root, word, node)
            assert word is not None 
            rootIndex = self.graph.transitions[root.unique_id][word]
            root = list(filter(lambda node: node.unique_id == rootIndex, self.graph.nodes))[0]
    
    def prefix(self, node :Node, k :int):
        if k == 0 or node == self.graph.root:
            return [[]]
        result =  [] 
        def dfs(node, k, path):
            if k == 0 or node == self.graph.root:
                result.append(path)
                return 
            for parent in node.parents:
                dfs(parent, k-1, [self.graph.getTransitionLabel(parent, node)] + path)

        dfs(node, k, [])
        return result
    
    def suffix(self, node: Node, k :int) -> set:
        if k == 0 or node == self.graph.root:
            return [[]]
        result =  [] 
        def dfs(node, k, path):
            if k == 0 or node == self.graph.root:
                result.append(path)
                return 
            for child in node.children:
                label = self.graph.getTransitionLabel(node, child)
                if label is not None:
                    dfs(child, k-1, path + [label])

        dfs(node, k, [])
        return set([ " ".join(path) for path in result])
    

class KTail:
    def __init__(self) -> None:
        self.tree =  PrefixTree()
    
    def add(self, trace):
        self.tree.add(trace)

    @property 
    def initialState(self):
        return self.tree.graph.root

    @property
    def states(self):
        return self.tree.graph.nodes
    
    @property
    def transitions(self):
        return self.tree.graph.transitions
    
    def k_tails(self,  k: int):
        if k == 0:
            return
        tree = self.tree 
        # print(len(tree.graph.nodes))
        for i in range(len(tree.graph.nodes)): 
            for j in range(i+1, len(tree.graph.nodes)):
                node1 = tree.graph.nodes[i]
                node2 = tree.graph.nodes[j]
                suffix1 = tree.suffix(node1, k)
                suffix2 = tree.suffix(node2, k)
                if suffix1 == suffix2 and len(suffix1) > 0:
                    # print(len(tree.graph.nodes))
                    tree.graph.merge(node1, node2)
                    # print(len(tree.graph.nodes))
                    # print("merge", node1.unique_id, node2.unique_id)
                    self.k_tails(k)
                    return
        return 
    
    def visualize(self, k, workdir):
        # assert len(self.states) > 1 
        states = set()
        labels = set()
        string_transitions = dict()
        for from_state in self.transitions:
            real_from_state = list(filter(lambda node: node.unique_id == from_state, self.states))[0]
            if not self.tree.graph.isConnect(self.initialState, real_from_state):
                continue
            if self.states.index(real_from_state) not in string_transitions:
                string_transitions[str(self.states.index(real_from_state))] =  dict() 
            for label in self.transitions[from_state]:
                    if label is None:
                        continue
                    to_state = self.transitions[from_state][label]
                    real_to_state = list(filter(lambda node: node.unique_id == to_state, self.states))[0]
                    states.add(str(self.states.index(real_from_state)))
                    states.add(str(self.states.index(real_to_state)))
                    req_label = str(label)
                    labels.add(req_label)
                    if req_label not in string_transitions[str(self.states.index(real_from_state))]:
                        string_transitions[str(self.states.index(real_from_state))][req_label] = set() 
                    string_transitions[str(self.states.index(real_from_state))][req_label].add(str(self.states.index(real_to_state)))
        for from_state in string_transitions:
            for label in string_transitions[from_state]:
                string_transitions[from_state][label] = list(string_transitions[from_state][label])

        initialState = str(self.states.index(self.initialState))
        nfa = VisualNFA(
            states= states,
            input_symbols= labels,
            transitions= string_transitions,
            initial_state = initialState,
            final_states = set(),
        )
        
        nfa.show_diagram(filename = f"{workdir}/FSM-K-Tail-{k}.dot", view=False, format_type="pdf")

        result = {
            "states": list(states),
            "statemachine":string_transitions,
            "initialState":initialState
        }
        json.dump(result, open(f"{workdir}/FSM-K-Tail-{k}.json", "w"))


def translate_trace(trace):
    result = []
    for item in trace:
        funcName =  item[0]
        assert isinstance(funcName, str)
        result.append(funcName)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--workdir", type=str, required=True)
    parser.add_argument("--k", type=int, required=True)
    args = parser.parse_args()
    traces = json.load(open(args.input, "r"))
    ktail = KTail()
    for trace_id in traces:
        ktail.add(translate_trace(traces[trace_id]))
    import time 
    start_time = time.time()
    ktail.k_tails(args.k)
    print("--- %s seconds ---" % (time.time() - start_time))
    # ktail.visualize(args.k, args.workdir)

if __name__ == "__main__":
    main() 
