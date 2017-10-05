#!/usr/bin/env python2
"""Create certificates for all domains managed by this container."""
import collections
import os.path
import shutil
import subprocess
import sys


DOMAIN2BACKEND_MAP = "/usr/local/etc/haproxy/domain2backend.map"
LE_CLIENT = "/usr/bin/certbot"
WEBROOT = "/var/lib/haproxy"
KEY_SIZE = "4096"


def read_domain_map(map_path):
    """Parse haproxy domain map file so we know what domains we need certs for."""
    result = collections.defaultdict(list)

    with open(map_path, 'r') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            try:
                domain, backend = line.split()
            except ValueError:
                continue

            result[backend].append(domain)

    return result


def reload_haproxy():
    """Gracefully reload haproxy."""
    print "Reloading..."
    return subprocess.check_call(["pkill", "-1", "-f", "haproxy"])


def create_or_renew_cert(domains, test=False):
    """Handle letsencrypt certificates for a single domain."""
    cmd = [
        LE_CLIENT, 'certonly',
        '--agree-tos',
        '--email', os.environ['EMAIL'],
        '--keep-until-expiring',
        '--non-interactive',
        '--rsa-key-size', os.environ.get('KEY_SIZE', KEY_SIZE),
        '--text',
        '--webroot', '--webroot-path', WEBROOT,
    ]

    for domain in domains:
        cmd.extend(['-d', domain])

    if test:
        cmd.extend(['--test-cert'])

    print "Running: %s" % cmd
    # TODO: if this errors, we need to stop or we exaust api limits
    r = subprocess.call(cmd)

    return r == 0


def generate_dh_params(domain, dh_param_root, key_size):
    """Improve security with per-cert params."""
    # generate dh-params if they do not exist
    domain_dhparam = os.path.join(dh_param_root, domain + "-dhparam.pem")

    if os.path.exists(domain_dhparam):
        return domain_dhparam

    print "Generating DH parameters, %s" % domain
    # TODO: don't block here
    subprocess.check_call([
        'openssl', 'dhparam',
        '-outform', 'PEM',
        '-out', domain_dhparam, key_size,
    ])

    return domain_dhparam


def concat_haproxy_certs(domains, live_cert_root, haproxy_cert_root, domain_dh_param):
    """Create a single file per-domain that haproxy can use."""
    live_domain_dir = os.path.join(live_cert_root, domains[0])

    privkey = os.path.join(live_domain_dir, 'privkey.pem')
    fullchain = os.path.join(live_domain_dir, 'fullchain.pem')

    # TODO: something about ocsp?

    if not domain_dh_param:
        raise ValueError("No dh param given")

    combined_cert = os.path.join(haproxy_cert_root, domains[0] + '.pem')
    print "Creating: %s" % combined_cert
    with open(combined_cert, 'wb') as wfd:
        for fname in [privkey, fullchain, domain_dh_param]:
            with open(fname, 'rb') as fd:
                shutil.copyfileobj(fd, wfd)

    return combined_cert


def main():
    """Manage letsencrypt certificate for HAproxy."""
    if not os.path.exists(WEBROOT):
        os.makedirs(WEBROOT)

    le_root = '/etc/letsencrypt'

    # TODO: create empty dirs for haproxy certs, dh_params, etc.
    live_cert_root = os.path.join(le_root, "live")
    if not os.path.exists(live_cert_root):
        # TODO: run certbot register?
        pass

    dh_param_root = os.path.join(le_root, 'dhparam')
    if not os.path.exists(dh_param_root):
        os.makedirs(dh_param_root)

    haproxy_cert_root = os.path.join(live_cert_root, 'haproxy')
    if not os.path.exists(haproxy_cert_root):
        os.makedirs(haproxy_cert_root)

    # print info about all our certificates
    subprocess.check_call([LE_CLIENT, 'certificates'])

    num_errors = 0
    num_domains = 0
    for backend, domains in read_domain_map(DOMAIN2BACKEND_MAP).items():
        # TODO: combine multiple domains into one cert?
        print("%s: %s" % (backend, domains))

        success = create_or_renew_cert(domains)
        if not success:
            num_errors += len(domains)
            continue

        domain_dhparam = generate_dh_params(
            domain=domains[0],
            dh_param_root=dh_param_root,
            key_size=KEY_SIZE,
        )

        concat_haproxy_certs(
            domains=domains,
            live_cert_root=live_cert_root,
            domain_dh_param=domain_dhparam,
            haproxy_cert_root=haproxy_cert_root,
        )

        num_domains += len(domains)

    if num_errors:
        print("There were errors!")

    if not num_domains:
        return 0

    # print info about all our certificates
    subprocess.check_call([LE_CLIENT, 'certificates'])

    # TODO: enable ssl portion of frontend in the config

    reload_haproxy()

    return 0


if __name__ == '__main__':
    sys.exit(main())
