# SEITON for Nextcloud

`seiton acl sync` (cli/seiton_acl.py, core/acl_nextcloud.py) copies a project's `.seiton/ACLs.md` into a
Team folder with "advanced permissions". The app `seiton` closes the one gap Nextcloud
leaves: who may only work deep down gets read on the way there, and an entry created later
on that way would inherit that read. The app locks such entries the moment they are created,
moved or copied there.

## Install the app (Nextcloud admin, once)

Copy `seiton/` into the server's `custom_apps/` (owned by the web server user), then

    occ app:enable seiton

Needs the Team folders app (groupfolders). Tested with Nextcloud 32 (Team folders 20.1) and
Nextcloud 35 from All-in-One (Team folders 23.0.1); 33 and 34 are not tested.

The app was called `myos_acl` until 2026-11-14. Its id cannot change, so `seiton` is a new
app. Coming from `myos_acl`: `occ app:disable myos_acl`, install `seiton` as above, and set
`core_url` and `core_secret` again under `seiton` (see below); the old values under `myos_acl`
are not read. Projects still under `.MyOS` need `.seiton`: `python3 cli/migrate_name.py --apply
<folder>` on a desktop, then let the sync client carry it up.

## What `seiton acl sync` needs on the server

- a Team folder with advanced permissions switched on, given to a group of everyone involved
- for the account that syncs: "manage advanced permissions" on that folder, and read on all of it
- an app password for that account (personal settings, Security)

## Test

`tests/test_seiton_app.py` runs against a test instance only (it changes the Team folder's
rules); see its docstring. Without `SEITON_NC_TEST_URL` (or the old `MYOS_NC_TEST_URL`) it is
skipped.

## The SEITON core next to Nextcloud

The core runs as its own container (`cloud/service/`, see "Designdocument SEITON Core
Service.md"). It reads the Team folder with the service account into a shadow tree (folders
and `.seiton` files) and rebuilds it when the folder's ETag changes. `seiton` passes
`GET /ocs/v2.php/apps/seiton/api/v1/{lens,bear,level,birth,tags}?path=` on with the logged-in
account (lib/Controller/CoreController.php); the browser never talks to the container. The project's `.seiton` must lie in the Team folder
(sync client or browser), with `Nextcloud.md` naming the accounts.

    docker buildx build --load -f cloud/service/Dockerfile -t seiton-core:dev .   # repo root
    docker network create seiton-net && docker network connect seiton-net <nextcloud container>
    docker run -d --name seiton-core --network seiton-net --env-file core.env seiton-core:dev
    occ config:system:set trusted_domains <n> --value=<nextcloud container>
    occ config:app:set seiton core_url --value=http://seiton-core:8080
    occ config:app:set seiton core_secret --sensitive --value=<SEITON_CORE_SECRET>

`seiton` tells the core of every change in a Team folder (POST /changed; the core decides
what matters), so it starts at once; it also looks at the folder's ETag every
`SEITON_SHADOW_POLL` seconds (default 60) for what no one told.
After each change of the Team folder the core does what `seiton acl sync` does
(core/nextcloud_sync.py) with the service account: a folder made later gets its rights from
`ACLs.md` within seconds, and an `ACLs.md` edited in the cloud changes the rules - unless it
leaves no one who may change the rights (then most likely broken: nothing is sent).
`seiton acl sync` from a desktop stays possible and does the same.

The tags of each project's `Tags.md` the core makes as Nextcloud's collaborative tags (one
list for the instance; never removed). The row of SEITON folders shows the tags a folder's
project suggests; a click shows only what carries the tag.

In Files the view "Perspectives" (left bar, `src/lens.js`) shows the turned tree:
departments, their folders, the shelf with the projects one may read, then the real
folders and files - opening, downloading, renaming and deleting act on the real ones. A
folder opens at its turned path, so the breadcrumbs stay in the lens. Where the department
folder is not born in a project, the project's own folder is shown read-only, with the
department folder above it as an embryo: a click bears it (with every missing level, as the
core plans it), dropping files on it bears it and puts them in. The view goes again for an account the core does not know.

`core.env` (mode 600): `SEITON_CORE_SECRET` (24 characters at least), `SEITON_NC_URL`
(`http://<nextcloud container>`), `SEITON_NC_USER`, `SEITON_NC_PASSWORD` (an app password of the
service account: a person of the role Admin), `SEITON_NC_FOLDER`, optionally `SEITON_SHADOW_POLL`
(seconds, default 60). The same names with `MYOS_` are still read. No port is published. After
updating the app: `occ app:disable seiton && occ app:enable seiton`, so Nextcloud reads its new
routes.

## Nextcloud All-in-One (AIO)

AIO keeps Nextcloud in the container `nextcloud-aio-nextcloud` and installs the newest major
version (an AIO update moves to the next one). The same steps, with these names:

    occ() { docker exec -u www-data nextcloud-aio-nextcloud php occ "$@"; }
    occ app:install groupfolders
    docker cp seiton nextcloud-aio-nextcloud:/var/www/html/custom_apps/
    docker exec nextcloud-aio-nextcloud chown -R www-data:www-data /var/www/html/custom_apps/seiton
    occ app:enable seiton
    docker run -d --name seiton-core --network nextcloud-aio --env-file core.env seiton-core:dev
    occ config:system:set trusted_domains 10 --value=nextcloud-aio-apache   # AIO sets 1 and 2 itself

The core joins AIO's own network `nextcloud-aio`; in `core.env`
`SEITON_NC_URL=http://nextcloud-aio-apache:<APACHE_PORT>` (11000 unless AIO was started with
another). AIO's password policy is on: the service account's app password is fine, test
accounts need long passwords.

## The row of SEITON folders

Above the file list the app shows the SEITON folders of the current folder, born ones in full
colour, embryos pale; clicking an embryo gives birth to it as Scope does (the folder, then the
files and hidden folders of that template level). Born SEITON folders leave the list below
(Nextcloud counts them as "hidden" there). Embryos show only where one may create.

`seiton acl sync` - or the core after each change - uploads per project a folder per embryo, `.seiton/Embryos/<embryo>/`, holding what
its birth copies (the files and hidden folders of that template level; its visible
subfolders are the deeper embryos), and `.seiton/Embryos.json` (the template tree and a hash
per file, the sync's bookkeeping) (core/cloud_embryos.py). Everyone with rights in the
project may list `.seiton/Embryos/`, each embryo's folder only who may read the folder it
becomes, as Scope shows embryos: who may do nothing in `/00_Admin` sees neither that embryo
nor its template. Nothing else of `.seiton` comes with it. What manages rights and the sync in
any `.seiton` (`ACLs.md`, `ACLs-history`, `Nextcloud.md`, `Embryos.json`, `Embryos/`) may only
be written by who has `change` on that `ACLs.md` - so the account that syncs needs it too.
Which SEITON folders a level holds and what a birth creates and copies, the core answers
(`level`, `birth`; cloud/service/level.py, by the same code as Scope); the browser creates
the folders and copies from `.seiton/Embryos/` on the server with the user's own rights.

The browser part is `src/main.js`, built to `js/seiton-main.js` (committed, so installing
needs no Node):

    cd cloud/nextcloud/seiton && npm install && npm run build
