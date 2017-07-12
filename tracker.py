#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  tracker.py
#
#  Copyright 2017
#  Author = "Djydo"
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

__author__ = "Djydo"
__license__ = "GPL"

import socket
import select

port = [5002, 5003, 5004, 5005, 5006, 5007]


clients = {}  # creates a dictionary (PORT:socket family) key-value pair
connected = []  # creates a list of ports for connected clients

tracker_port = 5000


def get_index(cl_port, all_clients):
    for client_index in range(len(all_clients)):
        if all_clients[client_index] == cl_port:
            return client_index


if __name__ == "__main__":

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('127.0.0.1', tracker_port))
    serverSocket.listen(5)

    print ('tracker started...')

    # clients = {}     # creates a dictionary (PORT:socket family) key-value pair
    # connected = []   # creates a list of ports for connected clients
    clients[tracker_port] = serverSocket  # add server to the dictionary

    while True:
        # pass values (sockets family) from the clients dictionary to select.select
        readable, writable, exception = select.select(clients.values(), [], [])
        for sock in readable:
            if sock == serverSocket:  # TRUE if the connection is from new client
                clientSock, address = serverSocket.accept()  # server accepts the new connection
                port = address[1]  # extracts PORT number from address
                print(port)  # prints PORT on the CLI

                msg = 'connection received from ' + str(port) + '\n'
                print(msg)

                connected.append(port)  # append port to list of connected clients
                clients[port] = clientSock  # create a dict of PORT: socket info

                # get the index of the new client and send its index along with welcome message
                for index in range(len(connected)):
                    if connected[index] == port:
                        client_position = index
                        welcome_msg = str(client_position) + ' on PORT: ' + str(port)
                        clientSock.send(welcome_msg)


            else:
                try:
                    # ensures that at least two clients are connected before forwarding messages
                    if len(connected) > 1:
                        data = sock.recv(4096)
                        print ('Connected Clients: {}'.format(connected))  # print connected clients

                        port = sock.getpeername()[1]  # node address: tuple ('ip address', port)
                        print('sender: {}'.format(port))  # port number of node
                        source_index = get_index(port, connected)  # gets sender's index
                        source_port = connected[source_index]  # gets sender's port from list of connected nodes

                        '''
                        The destination port is computed - if the node happens to be last, destination is first node
                        '''
                        if source_port == connected[-1:][0]:  # if source is last on the list
                            dest_port = connected[0]
                        else:
                            dest_port = connected[source_index + 1]

                        '''
                        This portion  handles TOKEN, Election, and leader passing among connected nodes
                        '''
                        if data[:5] == 'TOKEN':
                            dest_sock = clients[dest_port]
                            msg = 'TOKEN from: ' + str(source_port)
                            dest_sock.send(msg)
                            print ('TOKEN from {} to {}'.format(source_port, dest_port))

                        elif data[:8] == 'Election':
                            dest_sock = clients[dest_port]
                            msg = data
                            dest_sock.send(msg)
                            print ('{}{}'.format(source_port, dest_port))

                        elif data[:6] == 'leader':
                            dest_sock = clients[dest_port]
                            msg = data
                            dest_sock.send(msg)
                            print ('{}{}'.format(source_port, dest_port))
                            
                except KeyboardInterrupt:
                    print ("Exit by User. Node disconnected...")

                # except Exception as err_msg:
                except socket.error as err_msg:
                    '''
                    Exception occurs if a node is terminated abruptly or socket of a node is disconnected
                    '''
                    port = sock.getpeername()[1]
                    source_index = get_index(port, connected)  # gets sender's index (disconnected node)

                    if source_index == 0:
                        source_port = connected[-1:][0]  # sender changed to last node if first node is disconnected
                    else:
                        source_port = connected[
                            source_index - 1]            # change sender's port to previous of disconnected node

                    clients.pop(connected[source_index])  # remove disconnected node from dictionary
                    connected.remove(port)  # remove disconnected node from list

                    print(connected)
                    # print(clients)
                    '''
                    # if sender is last on the clients' list, the next node is first node
                    '''
                    if source_port == connected[-1:][0]:
                        dest_port = connected[0]
                    else:
                        dest_port = connected[source_index]

                    dest_sock = clients[dest_port]

                    dest_sock.send(msg)  # send message to destination to keep loop going

                    print("Node disconnected, socket error! {}".format(err_msg))  # error message on CLI
                finally:
                    pass
