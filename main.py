import os
import sys
import socket
import argparse
import ssl
import re
import ftplib

def is_valid_url(url):
    #Regex to check if it's valid. I hate Regex.
    url_regex = re.compile(r'^(http|https|ftp)://([A-Za-z0-9.-]+)(:[0-9]+)?(/.*)?$', re.IGNORECASE)

    return re.match(url_regex, url) is not None

def download_ftp(host, path, out, username, password, v):
    try:
        if v == True: print(f'Connecting to FTP server {host}')
        with ftplib.FTP(host) as ftp:
            ftp.login(username, password)
            if v == True: print(f'Connected to FTP server {host}')
            fname = os.path.basename(path)
            outpath = os.path.join(out, fname)
            with open(outpath, 'wb') as f:
                ftp.retrbinary(f'RETR {path}', f.write)
                if v == True: print(f'Downloaded {path} to {outpath}')
    except Exception as e:
        print(f'Failed to download: {e}')
        sys.exit(1)

def download(url, outdir='.', v=False):
    protocols = ['http', 'https', 'ftp']

    if not is_valid_url(url):
        print('Invalid URL')
        sys.exit(1)
    if v == True: print('URL is valid.')
    if v == True: print(f'Downloading {url} to {outdir}')
    try:
        filename = url.split('/')[-1] or 'foo'
        outpath = os.path.join(outdir, filename)

        if not (url.startswith(p) for p in protocols):
            print(f'Unsupported protocol. Supports {", ".join(protocols)}')
            sys.exit(1)
        redirectc = 0
        while redirectc < 5:
            url_parts = url.split('://', 1)[1].split('/', 1)
            host = url_parts[0]
            path = f'/{url_parts[1]}' if len(url_parts) > 1 else '/'

        
            if url.startswith(protocols[1]):
                port = 443
            elif url.startswith(protocols[0]):
                port = 80
            elif url.startswith(protocols[2]):
                port = 21
            else:
                print('Unsupported protocol')
                sys.exit(1)

            if ':' in host:
                host, port = host.split(':', 1)
                port = int(port)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                if v == True: print(f'Trying to connect to {host} on port {port}')
                s.connect((host, port))
                
                #https needs SSL stuff
                if url.startswith(protocols[1]):
                    context = ssl.create_default_context()
                    s = context.wrap_socket(s, server_hostname=host)

                if v == True: print(f'Connected to {host} on port {port}')
                
                if url.startswith(protocols[1]) or url.startswith(protocols[0]):
                    req = f'GET {path} HTTP/1.0\r\nHost: {host}\r\nConnection: close\r\nUser-Agent: Python0\r\n\r\n'
                elif url.startswith(protocols[2]):
                    user = input('Username: ')
                    passwd = input('Password: ')
                    download_ftp(host, path, outdir, user, passwd, v)
                    break
                else:
                    print('Unsupported protocol')
                    sys.exit(1)

                s.sendall(req.encode('utf-8'))

                res = b''
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    res += data

            finally:
                s.close()
        
            if url.startswith(protocols[0]) or url.startswith(protocols[1]):
                header, __, body = res.partition(b'\r\n\r\n')
                if v == True: print(header)

                #Stuff moved permenantly a bunch so deal with that
                if b'HTTP/1.1 30' in header or b'HTTP/1.0 30' in header:
                    location = [line for line in header.split(b'\r\n') if b'Location:'in line]
                    if location:
                        redirect = location[0].split(b': ', 1)[1].decode('utf-8')
                        if v == True: print(f'Redirecting to {redirect}')
                        url = redirect
                        redirectc += 1
                        continue
                elif b'200 OK' in header:
                     with open(outpath, 'wb') as f:
                        f.write(body)
                        print(f'Downloaded {url} to {outpath}')
                     return
            else:
                body = res

            if not body:
                print('Failed to get the file, no body')
                sys.exit(1)


    except Exception as e:
        print(f'Failed to download: {e}')
        sys.exit(1)

if __name__ == '__main__':
    #Argpares init
    parser = argparse.ArgumentParser(description='Download a file from the internet')
    parser.add_argument('-o', '--outdir', help='Output directory. Defaults to .', default='.')
    parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')
    args = parser.parse_args()
    
    url = input('URL: ')
    #Check for the directory
    if not os.path.isdir(args.outdir):
        print(f'{args.outdir} is not a directory')
        sys.exit(1)

    #Check for the URL
    if not url:
        print('URL is required')
        sys.exit(1)
    
    download(url, args.outdir, args.verbose)
