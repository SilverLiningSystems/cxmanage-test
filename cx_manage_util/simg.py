"""python for manipulating Calxeda SIMG headers"""
import struct
import argparse

def create_simg(infile_path, outfile_path, daddr=0):
    """Create an SIMG version of a file
    
    Assumes version, hdrfmt, daddr and crc32 are all 0.
    """
    contents = open(infile_path).read()
    string = struct.pack('<4sHHIIIII',
            'SIMG',         #magic_string
            0,              #hdrfmt
            0,              #version
            28,             #imgoff
            len(contents),  #imglen
            daddr,          #daddr
            0xffffffff,     #flags
            0x00000000)     #crc32
    
    with open(outfile_path, 'w') as outfile:
        outfile.write(string)
        outfile.write(contents)

def display_simg(infile_path):
    """Display the SIMG header of a file"""
    header = open(infile_path).read(28)
    tup = struct.unpack('<4sHHIIIII', header)
    print('magic:       %s' % tup[0])
    print('hdrfmt:      %d' % tup[1])
    print('version:     %d' % tup[2])
    print('imgoff:      %d' % tup[3])
    print('imglen:      %d' % tup[4])
    print('daddr:       0x%08x' % tup[5])
    print('flags:       0x%08x' % tup[6])
    print('crc32:       0x%08x' % tup[7])

def build_parser():
    """build an argparse parser"""
    parser = argparse.ArgumentParser(description='SIMG tool')
    subparsers = parser.add_subparsers()

    create = subparsers.add_parser('create')
    create.add_argument('-d', '--daddr',
                        help='Load destination address',
                        default=0,
                        type=lambda x : int(x, 16))
    create.add_argument('infile_path', help='path of input file')
    create.add_argument('outfile_path', help='path of output file')
    create.set_defaults(command='create')

    display = subparsers.add_parser('display')
    display.add_argument('infile_path', help='path of file to display')
    display.set_defaults(command='display')

    return parser

def main():
    """parse arguments and go"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == 'create':
        create_simg(args.infile_path, args.outfile_path, args.daddr)
    elif args.command == 'display':
        display_simg(args.infile_path)
    else:
        print('how did you get here?')

if __name__ == '__main__':
    main()
