#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  client.py
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


import socket
import sys
import time
import tracker


def send_message(server, msg):
    if msg == 'TOKEN':
        server.send('TOKEN')
        print('Sending TOKEN')
    else:
        server.send(msg)
        print('Sending {}'.format(msg))


# main function
if __name__ == "__main__":

    print('Enter node in range of 0-5:\nFor Instance: \'0\'  (without quote) for first node... ')
    print('===========================================================')
    try:
        position = int(input('Enter the node instance: '))

        port = tracker.port[position]

        host = 'localhost'
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        clientSocket.bind((host, port))
        clientSocket.connect((host, 5000))

    except KeyboardInterrupt:
        print('node disconnected by user')
        clientSocket.close()
        sys.exit()

    except NameError:
        print('sorry, input cannot be processed')
        sys.exit()

    except socket.error as e:
        print('Unable to connect')
        print(e)
        sys.exit()

    except:
        print('Unable to process. Exiting...')
        sys.exit()

    message = clientSocket.recv(1024)  # received from server
    print('client {}'.format(message))

    count = 0
    active_clients = []
    next_to_leader = 0



    if message[:1] == '0':
        time.sleep(20)                           # puts a little hold on client before starting out the election process
        print('starting election...')
        send_message(clientSocket, 'Election:' + str(port))  # first client initiates election


    while True:
        try:

            data = clientSocket.recv(1024)  # reset message and get new message

            '''
            Performs election
                - receives 'Election' message and concatenated process number of nodes that have participated
                - if the election originates from the client, the leader is selected and printed
                - Once leader is selected, the message is circulated
            '''
            if data[:8] == 'Election':
                active_clients = (data.split(':', 6))[1:]  # remove "Election" string and generate a list of clients

                if port == int(active_clients[0]):  # check for the first client that started the election process
                    leader = max(active_clients)    # highest process number becomes the leader
                    current_leader = int(leader)         # save current leader

                    print ('leader = {}'.format(leader))
                    time.sleep(5)                     # wait a little before sending leader information
                    clientSocket.send('leader = ' + str(leader) + ':' + str(port)) # forward to other nodes
                else:
                    print('current port {}'.format(port))
                    time.sleep(5)                             # wait a little before sending election message
                    print('Clients already participated in {}'.format(data)) # print the circulated election message
                    clientSocket.send(data + ':' + str(port))  # keep circulating the election message
                continue


            '''
            Print leader on each node
                - checks if the nodes have been informed (informed clients) about the leader
                - if yes, stop the circulation and commence TOKEN passing
                - if no, print and keep circulating
            '''
            if data[:6] == 'leader':
                informed_clients = (data.split(':', 6))[1:]
                leader_info = (data.split(':', 6))[0]

                if port == int(informed_clients[0]):
                    print('Election completed!')
                    time.sleep(3)                                       # wait a little before sending election message
                    leader = int(leader_info.split('=', 6)[1])          # save leader process number
                    send_message(clientSocket, 'TOKEN')                 # start passing the TOKEN

                else:
                    leader = int(leader_info.split('=', 6)[1])  # extract the leader process number
                    current_leader = leader
                    print(leader_info)                          # print the leader information
                    time.sleep(3)                               # wait a little before sending election message
                    clientSocket.send(data + ':' + str(port))   # keep circulating
                continue

            '''
            Token Passing
               - checks the data received if first part is TOKEN
               - activate timeout for the node if nothing is received
               - on first iteration for all nodes (except the first), capture the previous process number
               - set the previous node of the first client (node) to last on the list (active clients)
               --------------------------------------------------------------------------------------------
               - for newly joined client (whose active client's list is empty), activate election
               - for already connected clients, keep passing TOKEN
                  * check if the previous node is the same as the one when ring starts (compare with sender)
                  * if previous node is the leader, captures its detail
                  * if leader disconnects and NO TOKEN, the next node enters panic mode and activates timeout period
                  * if timeout elapses, election is activated
                  * other nodes in the ring also activates election after period of inactivity (NO TOKEN received)

            '''
            if data[:5] == 'TOKEN':

                clientSocket.settimeout(15)                    # set timeout if nothing (e.g TOKEN) is received

                # Captures the previous node of every client (on first iteration)
                if (count == 0) and message[:1] != '0':
                    prev_node = data.split(':', 6)[1]          # extract previous node from string
                    previous_node = int(prev_node.lstrip())
                    count += 1

                # captures the previous node of the first client
                elif active_clients[0]:
                    previous_node = int(active_clients[-1])  # last node after the latest election

                # handles new client connection
                if len(active_clients) == 0:
                    print("initiating election")
                    send_message(clientSocket, 'Election:' + str(port))

                # already connected clients continue passing TOKEN
                else:
                    print('{} received'.format(data))

                    sender = int((data.split(':', 6)[-1]).lstrip())

                    # check if sender is the same as previous node as at starting of the ring
                    if (previous_node == sender) and (data[:5] == 'TOKEN'):
                        send_message(clientSocket, 'TOKEN')

                        time.sleep(10)

                    # if leader leaves activate panic mode
                    elif (previous_node == leader) and (sender != previous_node):
                        next_to_leader = port
                        print("Leader has left! Panic Mode activated...")
                        clientSocket.settimeout(20)

                    # if a node (not leader) leaves continue to pass token
                    elif (previous_node != leader) and (sender != previous_node):
                        send_message(clientSocket, 'TOKEN')

                        time.sleep(10)

        except socket.timeout:

            # once the next node to the current leader time-out after not receiving TOKEN
            if next_to_leader:
                print("Initiating election...")
                send_message(clientSocket, 'Election:' + str(port))

            # other nodes in the ring time-out after not receiving TOKEN
            else:
                print("No TOKEN received! Initiating election...")
                send_message(clientSocket, 'Election:' + str(port))

        except KeyboardInterrupt:
            print('node disconnected by user')
            sys.exit()

        except Exception as e:
            print(e)
            sys.exit()
