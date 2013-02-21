#!/usr/bin/env python

# Copyright (c) 2012, Calxeda Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of Calxeda Inc. nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.


import glob
import json

from cxmanage_api.ip_discovery.ip_retriever import IPRetriever


def get_server_ips(ecme_list, aggressive=False, verbosity=0, 
                              multithreaded=True, **kwargs):
    """Convenience method for obtaining the server IP addresses
       from the ecme IP addresses provided. Creates an IPRetriever
       internally with the arguments provided. A single ecme address
       and the output from get_ecme_ips will also be accepted.
    """
    retriever_list = []

    if not hasattr(ecme_list, '__iter__'):
        ecme_list = [ecme_list]

    for ecme in ecme_list:
        if isinstance(ecme, IPRetriever):
            retriever_list.append(ecme)
        else:
            retriever_list.append(IPRetriever(ecme, aggressive, 
                                              verbosity, **kwargs))

    if multithreaded:
        for node in retriever_list:
            node.start()

        for node in retriever_list:
            node.join()
    else:
        for node in retriever_list:
            node.run()

    return [node.server_ip for node in retriever_list]
            

def map_config(path, node_list):
    """Loads the address information for all nodes from json 
       configuration files in the given directory and attempts 
       to match them to the nodes given in node_list.
    """
    node_table = dict((node.ecme_ip, node) for node in node_list)

    for node_path in glob.glob(path + '/node*'):
        with open(node_path, 'r') as json_file:
            json_data = json_file.read()
            config_data = json.loads(json_data)

            ecme_ip = config_data['ecme_host']
            server_ip = config_data['server_host']

            if ecme_ip in node_table:
                node = node_table[ecme_ip]

                if node._ip_pattern.match(server_ip):
                    node.server_ip = server_ip
