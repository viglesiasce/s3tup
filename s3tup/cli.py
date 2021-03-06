import argparse
import logging
import textwrap
import sys
import os

from s3tup.parse import load_config, parse_config

log = logging.getLogger('s3tup')
title = (
    "\n"
    "        _____ __             \n"
    "   ____|__  // /___  ______  \n"
    "  / ___//_ </ __/ / / / __ \ \n"
    " /__  /__/ / /_/ /_/ / /_/ / \n"
    "/____/____/\__/\____/ /___/  \n"
    "                   /_/         "
)

parser = argparse.ArgumentParser(
    description='s3tup: configuration management and deployment for AmazonS3')
parser.add_argument(
    'config_path',
    help='path to your configuration file')
parser.add_argument(
    '--dryrun',
    action='store_true',
    help='preview what will happen when this command runs')
parser.add_argument(
    '--rsync',
    action='store_true',
    help='only sync keys that have been modified or removed')
parser.add_argument(
    '-c',
    type=int,
    metavar='CONCURRENCY',
    help='number of concurrent requests (default: 5)')
verbosity = parser.add_mutually_exclusive_group()
verbosity.add_argument(
    '-v', '--verbose',
    action='store_true',
    help='increase output verbosity')
verbosity.add_argument(
    '-q', '--quiet',
    action='store_true',
    help='silence all output')
parser.add_argument(
    '--access_key_id',
    help='your aws access key id')
parser.add_argument(
    '--secret_access_key',
    help='your aws secret access key')


class WrappedFormatter(logging.Formatter):

    """Wrap log lines at 78 chars."""

    def format(self, record):
        formatted = super(WrappedFormatter, self).format(record)
        split = formatted.split('\n')
        return '\n'.join([textwrap.fill(l, 78) for l in split])


def main():

    """Command line interface entry point."""

    args = parser.parse_args()

    if not (args.quiet or args.verbose):
        handler = logging.StreamHandler()
        handler.setFormatter(WrappedFormatter('%(message)s'))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
    elif args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s',
                            level=logging.DEBUG)

    try:
        run(args.config_path, args.dryrun, args.rsync, args.c,
            args.access_key_id, args.secret_access_key)
    except Exception as e:
        if args.verbose:
            raise
        log.error('{}: {}'.format(sys.exc_info()[0].__name__, e))
        sys.exit(1)


def run(config, dryrun=False, rsync=False, concurrency=None,
        access_key_id=None, secret_access_key=None,):

    if access_key_id is not None:
        os.environ['AWS_ACCESS_KEY_ID'] = access_key_id
    if secret_access_key is not None:
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_access_key

    config = load_config(config)
    buckets = parse_config(config)

    log.info(title)

    for b in buckets:
        if concurrency is not None:
            b.conn.concurrency = concurrency
        b.sync(dryrun=dryrun, rsync=rsync)
