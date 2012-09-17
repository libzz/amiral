# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# This file deals with graphs
#
# Author:       Chris Browning <ckb6@cs.waikato.ac.nz>
# Version:      $Id$
#
# crcnetd is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# crcnetd is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# crcnetd; if not, write to the Free Software Foundation, Inc., 
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_events import *
from crcnetd._utils.ccsd_session import getSession, getSessionE
from crcnetd._utils.ccsd_server import exportViaXMLRPC
from crcnetd._utils.ccsd_service import getServiceInstance
ccs_mod_type = CCSD_SERVER
GRAPH_SERVER = "localhost:80"

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraph(session_id, graph_id, time_id):
    '''This returns everything the graph server needs to draw a graph'''

    session = getSessionE(session_id)
    
    #Get the graph type
    sql = "SELECT a.*, b.class_name AS filename2 FROM graph_type a, rrdbot_class b WHERE b.class_id=a.class_id AND graph_id=%s"
    #sql = "SELECT * FROM graph_type where graph_id=%s"
    res = session.query(sql, (graph_id))
    
    #Get the parts for the graph
    sql = "SELECT * FROM graph_parts where graph_id=%s ORDER BY graph_order"
    res2 = session.query(sql, (graph_id))

    #Get the time class
    sql = "SELECT * FROM graph_time where time_id=%s"
    res3 = session.query(sql, (time_id))

    return [res, res2, res3]

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getSnmpLogs(session_id):
    '''This returns a list of entries in the rrdbotlog view'''

    session = getSessionE(session_id)

    sql = "SELECT * FROM rrdbotlog ORDER BY timestamp DESC" 
    res = session.query(sql, ()) 
    return res
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def snmpDelete(session_id, host_id, class_id, num):
    '''This deletes a row in the snmp_discovery table'''

    session = getSessionE(session_id)

    sql = "DELETE FROM snmp_discovery WHERE host_id=%s AND class_id=%s AND num=%s" 
    session.execute(sql, (host_id,class_id, num)) 
    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def snmpDeleteHost(session_id, host_id):
    '''This removes a host from the snmp_discovery table'''
    session = getSessionE(session_id)

    sql = "DELETE FROM snmp_discovery WHERE host_id=%s" 
    session.execute(sql, (host_id)) 
    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def snmpFlush(session_id):
    '''This flushes the entire snmp_discovery table'''
    session = getSessionE(session_id)

    sql = "DELETE FROM snmp_discovery" 
    session.execute(sql, ()) 
    return 1
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getHostGraphs(session_id, host_id):
    '''This returns a list of graphs that are available to a host'''

    session = getSessionE(session_id)

    #-1 means all types of graphs
    if int(host_id) == -1:
        sql = "SELECT * FROM graph_group" 
        res = session.query(sql, ()) 
        res.sort(key=lambda obj:obj["group_name"].lower());
        return res

    sql = "SELECT DISTINCT b.group_id, b.group_name, a.host_id, a.host_name FROM graphview a LEFT JOIN graph_group b ON b.group_id=a.group_id WHERE host_id=%s" 
    res = session.query(sql, (host_id))
    res.sort(key=lambda obj:obj["group_name"].lower());
    return res
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getLinkGraphs(session_id, link_id=-1, graph_id=-1, all=True):
    global GRAPH_SERVER
    '''This returns graph data for a link'''
    session = getSessionE(session_id)
    link_id = int(link_id)
    graph_id = int(graph_id)
    
    if graph_id == link_id == -1:
        #This case is for a menu so return limited data
        sql = "SELECT DISTINCT link_id, description FROM graphview WHERE link_id!=0"
        res = session.query(sql, ())
    elif graph_id == -1:
        sql = "SELECT * FROM graphview WHERE link_id=%s"
        res = session.query(sql, (link_id))
    elif link_id == -1:
        sql = "SELECT * FROM graphview WHERE graph_id=%s AND link_id!=0"
        res = session.query(sql, (graph_id))
    else:
        sql = "SELECT * FROM graphview WHERE link_id=%s AND graph_id=%s" 
        res = session.query(sql, (link_id,graph_id))
    res.sort(key=lambda obj:obj["description"].lower())
    linkGraphs2 = []
    for link in res:
        newlink = {}
        newlink["link_id"] = link["link_id"]
        newlink["description"] = link["description"]
        if all:
            newlink ["host_id"] = link["host_id"]
            newlink ["host_name"] = link["host_name"]
            newlink ["graph_id"] = link["graph_id"]
            newlink ["group_id"] = link["group_id"]
            newlink ["title"] = link["title"]
            newlink ["num"] = link["num"]
            newlink ["description"] = link["description"]
            newlink ["ip_address"] = link["ip_address"]
        
            
        linkGraphs2.append(newlink)    
    return GRAPH_SERVER, linkGraphs2     
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphs(session_id, host_id=-1, group_id=-1, mirror='f'):
    global GRAPH_SERVER
    '''This returns data to draw graphs'''
    
    '''It also handles mirror in which both sides of a link are returned'''
    
    host_id = int(host_id)
    group_id = int(group_id)
    session = getSessionE(session_id)

    #Select table based on mirror
    if mirror == 't':
        table = "mirrorview"
    else:
        table = "graphview"
        
    if group_id == host_id == -1:
        sql = "SELECT * FROM %s" % table
        res = session.query(sql, ())
    elif group_id == -1:
        sql = "SELECT * FROM %s WHERE host_id=%%s" % table
        res = session.query(sql, (host_id))
    elif host_id == -1:
        sql = "SELECT * FROM %s WHERE group_id=%%s" % table
        res = session.query(sql, (group_id))
    else:
        sql = "SELECT * FROM %s WHERE host_id=%%s AND group_id=%%s" % table
        res = session.query(sql, (host_id,group_id))

    #Prune of pythons double up of data but keep all data
    #This loop saves time in php as it has to decode less
    graphs2 = []
    for graph in res:
        newgraph = {}
        newgraph ["host_id"] = graph["host_id"]
        newgraph ["host_name"] = graph["host_name"]
        newgraph ["graph_id"] = graph["graph_id"]
        newgraph ["group_id"] = graph["group_id"]
        newgraph ["title"] = graph["title"]
        newgraph ["num"] = graph["num"]
        newgraph ["description"] = graph["description"]
        newgraph ["ip_address"] = graph["ip_address"]

        if "num2" in graph.keys():
             newgraph ["host_id2"] = graph["host_id2"]
             newgraph ["host_name2"] = graph["host_name2"]
             newgraph ["num2"] = graph["num2"]
             newgraph ["ip_address2"] = graph["ip_address2"]
                
        graphs2.append(newgraph)    
        
    return GRAPH_SERVER, graphs2

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getTimes(session_id):
    '''Simple function to return all time classes'''

    session = getSessionE(session_id)
    sql = "SELECT * from graph_time"
    res = session.query(sql, ())
    res.sort()
    return res

    
def getHostList(session_id):
    ''' A custom getHostList that only returns hosts that there are graohs for'''
    session = getSessionE(session_id)
    sql = "SELECT DISTINCT host_id, host_name from graphview"
    res = session.query(sql, ())
    res.sort(key=lambda obj:obj["host_name"].lower())
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getEveryThing(session_id, host_id):
    '''This function returns everything needed for the graph interface'''
    
    '''Its purpose is to reduce the number of xmlrpc calls required'''
    
    '''It also removes double up infomation for speed in php'''
    x1 = time.time()

    
    hostList = getHostList(session_id)
    hostList2 = []
    for host in hostList:
        newhost = {}
        newhost["host_name"] = host["host_name"]
        newhost["host_id"] = host["host_id"]
        hostList2.append(newhost)
    if host_id == '' and len(hostList2) > 0:
        host_id = hostList2[0]["host_id"]
    elif host_id == '':
        host_id = 0

    server, linkGraphs = getLinkGraphs(session_id,-1,-1,False)

    hostGraphs = getHostGraphs(session_id, host_id)
    hostGraphs2 = []
    for graph in hostGraphs:
        newgraph = {}
        newgraph ["group_id"] = graph["group_id"]
        newgraph ["group_name"] = graph["group_name"]
        hostGraphs2.append(newgraph)    
    server, graphs = getGraphs(session_id)
    times = getTimes(session_id)
    pack = [hostList2, linkGraphs, hostGraphs2, graphs, times]
    return pack
   
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphserver(session_id):
    '''Simple function to return the graphserver'''
    return GRAPH_SERVER
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphGroups(session_id):
    '''Simple function to return all graph groups'''

    session = getSessionE(session_id)
    sql = "SELECT * from graph_group"
    res = session.query(sql, ())
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphTypes(session_id, group_id):
    '''Simple function to return all graph types in a group'''

    session = getSessionE(session_id)
    sql = "SELECT * from graph_type WHERE group_id=%s"
    res = session.query(sql, (group_id))
    return res

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphParts(session_id, graph_id):
    '''Simple function to return all graph parts of a graph'''

    session = getSessionE(session_id)
    sql = "SELECT * from graph_parts WHERE graph_id=%s ORDER BY graph_order"
    res = session.query(sql, (graph_id))
    return res    

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphPart(session_id, part_id):
    '''Simple function to return a graph part'''

    session = getSessionE(session_id)
    sql = "SELECT * from graph_parts WHERE part_id=%s"
    res = session.query(sql, (part_id))
    return res[0]     

@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphGroup(session_id, group_id):
    '''Simple function to return a group'''

    session = getSessionE(session_id)
    sql = "SELECT * from graph_group WHERE group_id=%s"
    res = session.query(sql, (group_id))
    return res[0]    
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphType(session_id, graph_id):
    '''Simple function to return a graph type'''

    session = getSessionE(session_id)
    sql = "SELECT * from graph_type WHERE graph_id=%s"
    res = session.query(sql, (graph_id))
    return res[0]    
    
@exportViaXMLRPC(SESSION_RO, AUTH_USER)
def getGraphVars(session_id, graph_id):
    '''Returns all vars that are defined'''

    session = getSessionE(session_id)
    sql = "SELECT varname from graph_parts WHERE graph_id=%s AND (type='DEF' OR type='CDEF')"
    res = session.query(sql, (graph_id))
    return res    

@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def updateGraphPartDetails(session_id, part_id, newDetails):
    """Updates the details of the Graph part.

    newDetails should be a dictionary containing only these class paramters
    that have changed and need to be updated in the database.
    """
    session = getSessionE(session_id)
        
    # Build SQL
    props = ["type", "colour", "text", "cf", \
        "filename", "varname", "graph_order"]

    (sql, values) = buildUpdateFromDict("graph_parts", props, newDetails, \
            "part_id", part_id)
        
    if values == None:
        # No changes made... ?
        return 1
    
    # Run the query
    session.execute(sql, values)

    return 1 
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def updateGraphTypeDetails(session_id, graph_id, newDetails):
    """Updates the details of the Graph type.

    newDetails should be a dictionary containing only these class paramters
    that have changed and need to be updated in the database.
    """
    session = getSessionE(session_id)
        
    # Build SQL
    props = ["title", "class_id", "virtical_label", "auto_comment", "rigid", "upper"]
    
    nulls= []

    if "upper" in newDetails and newDetails["upper"] == '':
        nulls.append("upper")

    (sql, values) = buildUpdateFromDict("graph_type", props, newDetails, \
            "graph_id", graph_id, False, nulls)
        
    if values == None:
        # No changes made... ?
        return 1
    
    # Run the query
    session.execute(sql, values)

    return 1    
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def addGraphGroup(session_id, clas):
    """Adds a new graph group to the database"""
    session = getSessionE(session_id)
    
    # Build query
    props = ["group_name"]
    (sql, values) = buildInsertFromDict("graph_group", props, clas)
    
    # Run query
    session.execute(sql, values)

    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def addGraphType(session_id, clas):
    """Adds a new graph type to the database"""
    session = getSessionE(session_id)
    
    # Build query
    props = ["title", "class_id", "group_id", "virtical_label", "auto_comment", "rigid", "upper"]
    
    nulls= []

    if "upper" in clas and clas["upper"] == '':
        nulls.append("upper")
    (sql, values) = buildInsertFromDict("graph_type", props, clas, False, nulls)
    
    # Run query
    session.execute(sql, values)

    return 1    
    
@exportViaXMLRPC(SESSION_RW, AUTH_USER)
def addGraphPart(session_id, clas):
    """Adds a new graph part to the database"""
    session = getSessionE(session_id)
    
    # Build query
    props = ["type", "colour", "text", "varname", "cf", "filename", "graph_id", "graph_order"]
    (sql, values) = buildInsertFromDict("graph_parts", props, clas)
    
    # Run query
    session.execute(sql, values)

    return 1       
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def removeGraphPart(session_id, part_id):
    """Removes a graph part from the database."""
    
    session = getSessionE(session_id)

    # Delete
    sql = "DELETE FROM graph_parts WHERE part_id=%s"
    res = session.execute(sql, (part_id))
    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def removeGraphType(session_id, graph_id):
    """Removes a graph type from the database."""
    
    session = getSessionE(session_id)

    # Delete
    sql = "DELETE FROM graph_type WHERE graph_id=%s"
    res = session.execute(sql, (graph_id))
    return 1
    
@exportViaXMLRPC(SESSION_RW, AUTH_ADMINISTRATOR)
def removeGraphGroup(session_id, group_id):
    """Removes a graph group from the database."""
    
    session = getSessionE(session_id)

    # Delete
    sql = "DELETE FROM graph_group WHERE group_id=%s"
    res = session.execute(sql, (group_id))
    return 1    

def ccs_init():
    global GRAPH_SERVER
    GRAPH_SERVER = "%s:%s" % (config_get("graphs", "host", "localhost"), \
        config_get("graphs", "port", "80"))

