#Copyright 2012 Calxeda, Inc.  All rights reserved.

""" Internal commands """

from controller import controller_config_ecc, controller_update_spiflash

def add_args(p):
    #spif command
    p['spifupdate'] = p['subparsers'].add_parser(
            'spifupdate', help='update spi flash')
    p['spifupdate'].add_argument('filename', help='path to file to upload')
    p['spifupdate'].add_argument('--no-reset', default=False,
            action='store_true', help='Don\'t reset the MC after updating')
    p['spifupdate'].set_defaults(func=spifupdate_command)

    #ecc command
    p['ecc'] = p['config_subs'].add_parser('ecc', help='enable or disable ECC')
    p['ecc'].add_argument('ecc_mode', help='ECC mode',
            type=lambda string: string.lower(), choices=['on', 'off'])
    p['ecc'].set_defaults(func=config_ecc_command)

def spifupdate_command(controller, args):
    # Do firmware update
    if controller_update_spiflash(controller, args.filename, args.no_reset):
        return 1
    return 0

def config_ecc_command(controller, args):
    """enable or disable ECC on a cluster or host"""
    if controller_config_ecc(controller, args.ecc_mode):
        return 1
    return 0
