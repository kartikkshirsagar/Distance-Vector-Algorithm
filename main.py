import threading
from asyncio import wait
from threading import Thread
from time import sleep
import math
import sys

lock = threading.Lock()
cv_lock = threading.Lock()
N = 4
sharedSpace = []
iterations = []
_CV = 0
_CV2 = 0


def printIters(_iterations,routers):
    # iter format (#iter,router_name,table_dict)
    _iterations.sort(key=lambda el: (el[0], el[1]))
    for i in range(len(_iterations)):
        print("---------------------------------")
        print("|\tIteration #{}\t\t|".format(_iterations[i][0]))
        print("|\tTable for Router {}\t|".format(_iterations[i][1]))
        for key in _iterations[i][2]:
            if _iterations[i][0]!=0:
                if _iterations[i-routers][2][key]!=_iterations[i][2][key]:
                    print("|\t{}\t{}*\t\t|".format(key,_iterations[i][2][key]))
                else:
                    print("|\t{}\t{}\t\t|".format(key, _iterations[i][2][key]))
            else:
                print("|\t{}\t{}\t\t|".format(key, _iterations[i][2][key]))
        print("---------------------------------")

def thread_func(routers, router_name, neighbours):
    # have to have the routing table
    global _CV
    neighbour_names = []
    for neighbour in neighbours:
        neighbour_names.append(neighbour[0])
    table = {}
    old_table = {}
    # init table
    for router in routers:
        table[router] = math.inf
    table[router_name] = 0
    for n in neighbours:
        table[n[0]] = n[1]
    # print("Router {} has been initialised\n".format(router_name))
    iterations.append((0, router_name, table.copy()))
    for i in range(N):
        # print("Iteration {}".format(i))
        # while _CV > 0:
        #     sleep(1)
        lock.acquire()
        sharedSpace.append((router_name, table.copy()))
        lock.release()
        while len(sharedSpace) < len(routers):  # if queue not full then wait
            # print("waiting on Q full")
            sleep(0.001)
        # now queue is full so router can read data from it
        neighbour_tables = []
        for t_ in sharedSpace:
            if t_[0] in neighbour_names:
                # get the new table of the neighbour and do calculations
                neighbour_tables.append(t_)
        old_table = table.copy()

        for vertex in table:  # for each node in the table
            ls = []
            for n in neighbour_tables:  # checking neighbour tables for finding a shorter path
                ls.append(table[n[0]] + n[1][vertex])  # bellman ford equation used here
            table[vertex] = min(min(ls), table[vertex])
        iterations.append((i + 1, router_name, table.copy()))  # iteration i means means bellman ford applied i times
        sleep(1)
        cv_lock.acquire()
        _CV += 1
        cv_lock.release()
        while _CV < (i + 1) * len(routers):
            """ for synchronising the routers, no router advances ahead until every router
              updates"""
            # print("waiting.. on cv")
            sleep(0.0001)
        try:
            lock.acquire()
            sharedSpace.remove((router_name, old_table))
            lock.release()
            sleep(0)
            global _CV2
            cv_lock.acquire()
            _CV2 += 1
            cv_lock.release()
            while _CV2 < (i + 1) * len(routers):
                """No router moves forward until all have removed their old values"""
                sleep(0.001)
        except:
            # if something goes wrong print info and release lock
            print((router_name, old_table))
            print(sharedSpace)
            lock.release()


def main_func():
    graph = {}  # to know the topology and neighbours
    print("Calculating.....")
    if len(sys.argv) > 1:
        file = sys.argv[1]
    else:
        file = 'routers.txt'
    with open(file, 'r') as f:
        inp = f.readlines()  # read all lines
    num_routers = int(inp[0].strip())
    router_names = list(map(str, inp[1].split()))  # get names of all routers
    # populate the graph
    for router in router_names:
        graph[router] = []
    i = 2
    while i<len(inp) and inp[i]!='EOF':
        from_, to, cost = inp[i].split()
        graph[from_].append((to, int(cost)))
        graph[to].append((from_, int(cost)))
        i += 1
    # print(graph)
    t_list = []
    for i in range(len(router_names)):
        thr = Thread(target=thread_func, name=router_names[i],
                     args=(router_names, router_names[i], graph[router_names[i]]))
        t_list.append(thr)
        thr.start()
    for thr in t_list:
        # print("JOINED", thr.name)
        thr.join()
    printIters(iterations,len(router_names))


main_func()
