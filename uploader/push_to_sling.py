#!/usr/bin/python3
import os
import requests
import getpass
import argparse
import getpass
from pathlib import Path
from datetime import datetime

HEADERS = {'cache-control': 'no-cache',
           'Accept': 'application/json'}

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description='''\
Bulk upload module for Pantheon 2. This tool will scan a directory recursively and upload relevant files. Relevancy is determined by examining the filename.

If the file suffix is .adoc or .asciidoc, then it is relevant if the extended suffix is one of these:
  .title.adoc
  .module.adoc
  .internal.adoc
For example: hotNewProduct.title.adoc

If the file suffix is anything else, then the file is relevant unless the extended suffix contains .ignore, like so:
  placeholderArt.ignore.jpg'
 
''')
parser.add_argument('--server', '-s', help='The Pantheon server to upload modules to, default http://localhost:8080', default='http://localhost:8080')
parser.add_argument('--repository', '-r', help='The name of the repository; this is a convenience for the user. If not specified, one will be autogenerated', default=getpass.getuser() + '_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
parser.add_argument('--user', '-u', help='Username for authentication, default \'demo\'', default='demo')
parser.add_argument('--password', '-p', help='Password for authentication, default \'demo\'. If \'-\' is supplied, the script will prompt for the password.', default='demo')
parser.add_argument('--directory', '-d', help='Directory to upload, default is current working directory. (' + os.getcwd() + ')', default=os.getcwd())
args = parser.parse_args()

pw = args.password
if pw == '-':
    pw = getpass.getpass()

print('Using server: ' + args.server)
print('Using repository: ' + args.repository)
print('--------------')

directory_in_str = args.directory
pathlist = Path(directory_in_str).glob('**/*.*')

for path in pathlist:
    # relative path to the current directory (with extension)
    relative_path_in_str = str(path.relative_to(Path.cwd()))
    # parent directory
    parent_dir_str = str(path.parent.relative_to(Path.cwd()))
    if parent_dir_str == '.':
        parent_dir_str = ''
    # file becomes a/file/name (no extension)
    base_name = path.stem

    url = args.server + "/content/repositories/" + args.repository
    if parent_dir_str:
        url += '/' + parent_dir_str

    # print('base name: ' + base_name)

    # Asciidoc content (treat as a module)
    if path.suffix == '.adoc' or path.suffix == '.asciidoc':
        print(path)
        if base_name.endswith(('.module', '.internal', '.title')):  # Should differentiate later
            url += '/' + path.name
            # print(url)
            data = {"jcr:primaryType": 'pant:module',
                    "jcr:title": base_name,
                    "jcr:description": base_name,
                    "sling:resourceType": 'pantheon/modules',
                    "pant:originalName": path.name,
                    "asciidoc@TypeHint": 'nt:file'}
            files = {'asciidoc': ('asciidoc', open(path, 'rb'), 'text/x-asciidoc')}

            # Minor question: which is correct, text/asciidoc or text/x-asciidoc?
            # It is text/x-asciidoc. Here's why:
            # https://tools.ietf.org/html/rfc2045#section-6.3
            # Paraphrased: "If it's not an IANA standard, use the 'x-' prefix.
            # Here's the list of standards; text/asciidoc isn't in it.
            # https://www.iana.org/assignments/media-types/media-types.xhtml#text

            r = requests.post(url, headers=HEADERS, data=data, files=files, auth=(args.user, pw))
            print(r.status_code, r.reason)
        else:
            print('Asciidoc file does not contain {\'.title\',\'.module\',\'.internal\'}, ignoring...')
        print()
    # Otherwise just upload as a regular file
    else:
        print(path)
        if not base_name.endswith('.ignore'):
            # print(url)
            files = {path.name: (path.name, open(path, 'rb'))}
            r = requests.post(url, headers=HEADERS, files=files, auth=(args.user, pw))
            print(r.status_code, r.reason)
        else:
            print('Resource file contains \'.ignore\', ignoring...')
        print()

print('Finished!')
