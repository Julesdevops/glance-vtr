import loggers
from export import convert, export

import argparse, os

loggers.initialize()

parser = argparse.ArgumentParser(
    prog='RectilinearGrid'
)

parser.add_argument('folder')
parser.add_argument('-r', '--render', action='store_true')

args = parser.parse_args()

if not os.path.isdir("outputs"):
    os.mkdir("outputs")
    os.mkdir("outputs/images")
    os.mkdir("outputs/json")
    os.mkdir("outputs/json/archives")
    os.mkdir("outputs/json/exports")

image_datasets = convert(args.folder)

export(image_datasets, args.render)
