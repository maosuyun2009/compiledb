#
#   compiledb-generator: Tool for generating LLVM Compilation Database
#   files for make-based build systems.
#
#   Copyright (c) 2017 Nick Diego Yamane <nick.diego@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ex: ts=2 sw=4 et filetype=python

import json
import os
import sys
from compiledb.parser import parse_build_log, Error


def __is_stdout(pfile):
    try:
        return pfile.name == sys.stdout.name or isinstance(pfile.name, int)
    except:
        return pfile == sys.stdout


def basename(stream):
    if __is_stdout(stream):
        return "<stdout>"
    else:
        return os.path.basename(stream.name)


def generate_json_compdb(instream=None, proj_dir=os.getcwd(), verbose=False, exclude_files=[], command_style=False):
    if not os.path.isdir(proj_dir):
        raise Error("Project dir '{}' does not exists!".format(proj_dir))

    print("## Processing build commands from {}".format(basename(instream)))
    result = parse_build_log(instream, proj_dir, exclude_files, verbose, command_style=command_style)
    return result


def write_json_compdb(compdb, outstream, verbose=False,
                      force=False, pretty_output=True):
    print("## Writing compilation database with {} entries to {}".format(
        len(compdb), basename(outstream)))

    # We could truncate after reading, but here is easier to understand
    if not __is_stdout(outstream):
        outstream.seek(0)
        outstream.truncate()
    json.dump(compdb, outstream, indent=pretty_output)
    outstream.write(os.linesep)


def load_json_compdb(outstream, verbose=False):
    try:
        if __is_stdout(outstream):
            return []

        # Read from beggining of file
        outstream.seek(0)
        compdb = json.load(outstream)
        print("## Loaded compilation database with {} entries from {}".format(
            len(compdb), basename(outstream)))
        return compdb
    except Exception as e:
        if verbose:
            print("## Failed to read previous {}: {}".format(basename(outstream), e))
        return []


def merge_compdb(compdb, new_compdb, check_files=True, verbose=False):
    def gen_key(entry):
        if 'directory' in entry:
            return os.path.join(entry['directory'], entry['file'])
        return entry['directory']

    def check_file(path):
        return True if not check_files else os.path.exists(path)

    orig = {gen_key(c): c for c in compdb if 'file' in c}
    new = {gen_key(c): c for c in new_compdb if 'file' in c}
    orig.update(new)
    return [v for k, v in orig.items() if check_file(k)]


def generate(infile, outfile, build_dir, exclude_files, verbose, overwrite=False, strict=False, command_style=False):
    try:
        r = generate_json_compdb(infile, proj_dir=build_dir, verbose=verbose, exclude_files=exclude_files,
                                 command_style=command_style)
        compdb = [] if overwrite else load_json_compdb(outfile, verbose)
        compdb = merge_compdb(compdb, r.compdb, strict, verbose)
        write_json_compdb(compdb, outfile, verbose=verbose)
        print("## Done.")
        return True
    except Error as e:
        print(str(e))
        return False
