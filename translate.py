#!/usr/bin/env python
# *-* encoding: utf-8 *-*

import json
import argparse
import os
import sys
from os.path import join
import re


def fix_lang_file(lang_file, keys):
    keys = list(keys)
    keys.sort()
    with open(lang_file, 'r') as fp:
        translations = json.load(fp)
    try:
        for key in translations:
            if key not in keys:
                print(f"ALERT: \"{key}\" unused!")
        for key in keys:
            if key not in translations:
                if lang_file.endswith('en.json'):
                    translations[key] = key
                else:
                    translations[key] = "TODO"
                print(f"Need to translate \"{key}\"")
    finally:
        with open(lang_file, 'w') as fp:
            json.dump(translations, fp, indent=2)


def get_keys_file(fl, expr):
    keys = set()
    with open(fl, 'r') as fp:
        for line in fp:
            line = line.strip()
            for match in expr.finditer(line):
                keys.add(match.group(1))
    return keys

def get_keys_py(fl):
    expr = re.compile('_\("(.+?)"\)')
    keys = get_keys_file(fl, expr)
    expr = re.compile('IllegalPlay\("(.+?)"\)')
    keys |= get_keys_file(fl, expr)
    expr = re.compile('IllegalPlay\(\'(.+?)\'\)')
    keys |= get_keys_file(fl, expr)
    return keys

def get_keys_js(fl):
    expr = re.compile('_\("(.+?)"\)')
    return get_keys_file(fl, expr)


def get_keys_html(fl):
    expr = re.compile('<my-translate msg="(.+?)">')
    return get_keys_file(fl, expr)


def get_keys(dir):

    keys = set()
    fkts = {'.py': get_keys_py,
            '.js': get_keys_js,
            '.html': get_keys_html}

    for root, dirs, files in os.walk(dir):
        for file in files:
            if file == sys.argv[0]:
                continue
            for ext, fkt in fkts.items():
                if file.endswith(ext):
                    keys |= fkt(join(root,file))
                    continue
    return keys

def main(lang_dir, dir):
    l_files = []
    for file in os.listdir(lang_dir):
        if file.endswith('.json'):
            l_files.append(join(lang_dir, file))

    keys = get_keys(dir)
    for lf in l_files:
        fix_lang_file(lf, keys)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str,
                        help="drirectory to scan",
                        default='./')
    parser.add_argument("--lang_dir", type=str,
                        help="drirectory of language files",
                        default='./htdocs/lang')
    args = parser.parse_args()



    main(args.lang_dir, args.dir)
