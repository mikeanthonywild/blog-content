Title: SSL certs for NGINX with Let's Enecrypt (Certbot) on FreeBSD
Date: 2016-05-23 19:12

There seems to be a myriad of guides on setting up Let's Encrypt, however it seems that the more obscure the platform (eg. FreeBSD and NGINX), the more complex the guides get. EFF's website details the [simplest solution](https://certbot.eff.org/#freebsd-nginx), which is covered here (albeit in a little more detail).

### 1. Install Let's Encrypt

The Let's Encrypt client is what helps verify the server and generate the certificates. As of May 2016, the *letsencrypt* tool became *certbot*, however the FreeBSD ports collection hasn't been updated to reflect this change yet.

Install the client package with `# pkg install py27-letsenecrypt`. Be warned that this drags in a whole bunch of Python packages.

### 2. Stop NGINX

Let's Encrypt needs to bind to port 80 to verify the server, so NGINX needs to be stopped with `# service nginx stop` before the certificate can be generated.

### 3. Run the client

Kick off the certificate generation process with `# letsencrypt certonly`. As there is currently no NGINX plugin for Let's Encrypt, go ahead and select option 2 *Automatically use a temporary webserver (standalone)*. Enter your email address so that Let's Encrypt can notify you of any issues, and then enter the domains (*Common Name* in X.509-speak) you wish to appear on this certificate. Let's Encrypt will store the new SSL certificates in */usr/local/etc/letsencrypt/example.com*. It also keeps a config file under */usr/local/etc/letsencrypt/renewal/example.com.conf* which is used for certificate regeneration.

### 4. Enable SSL in the NGINX config

If SSL is not already enabled in your NGINX config, it's a simple case of adding the following lines to your `server` block:

    listen 80;
    listen 443 ssl;

    ssl_certificate     /usr/local/etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /usr/local/etc/letsencrypt/live/example.com/privkey.pem;

### 5. Restart NGINX and test

Restart NGINX with `# service nginx start`, and provided there are no errors, you should be able to browse to [https://example.com](https://example.com) and examine your new SSL certificate.

### 6. Enable auto-renewal

Let's Encrypt certs have a lifetime of 90 days, however the renewal process is easy to automate with a cron job. First, stop NGINX again and check that Let's Encrypt can auto-renew all of your certificates with `# letsencrypt renew --dry-run`. EFF recommends that you run this twice a day to ensure there aren't any problems if a certificate is revoked. This can be done by running `# crontab -e` and adding the following line:

    42 00,12 * * * service nginx stop && letsencrypt renew --quiet && service nginx start

This schedules the renewal process for 42 minutes past midnight and midday. *42* is of course a random number to ensure that we don't overload Let's Encrypt's servers, as it's likely a lot of people will schedule the job on-the-hour.