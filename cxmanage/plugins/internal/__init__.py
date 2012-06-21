#Copyright 2012 Calxeda, Inc.  All rights reserved.

""" Internal commands """

from controller import controller_config_ecc

def add_args(p):
    #ecc command
    p['ecc'] = p['config_subs'].add_parser('ecc', help='enable or disable ECC')
    p['ecc'].add_argument('ecc_mode', help='ECC mode',
            type=lambda string: string.lower(), choices=['on', 'off'])
    p['ecc'].set_defaults(func=config_ecc_command)

def config_ecc_command(controller, args):
    """enable or disable ECC on a cluster or host"""
    if controller_config_ecc(controller, args.ecc_mode):
        return 1
    return 0
