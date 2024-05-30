# Apricot

`Apricot` is a proxy for delegating LDAP requests to an OpenID Connect backend.
The name is a slightly tortured acronym for: LD**A**P **pr**oxy for Open**I**D **Co**nnec**t**.

## Usage

Start the `Apricot` server on port 1389 by running:

```bash
python run.py --client-id "<your client ID>" --client-secret "<your client secret>" --backend "<your backend>" --port 1389 --domain "<your domain name>" --redis-host "<your Redis server>"
```

If you prefer to use Docker, you can edit `docker/docker-compose.yaml` and run:

```bash
docker compose up
```

from the `docker` directory.

### Using Redis [Optional]

You can use a Redis server to store generated `uidNumber` and `gidNumber` values in a more persistent way.
To do this, you will need to provide the `--redis-host` and `--redis-port` arguments to `run.py`.

### Configure background refresh [Optional]

By default Apricot will refresh the LDAP tree whenever it is accessed and it contains data older than 60 seconds.
If it takes a long time to fetch all users and groups, or you want to ensure that each request gets a prompt response, you may want to configure background refresh to have it periodically be refreshed in the background.

This is enabled with the `--background-refresh` flag, which uses the `--refresh-interval` parameter as the interval to refresh the ldap database.

### Using TLS [Optional]

You can set up a TLS listener to communicate with encryption enabled over the configured port.
To enable it you need to configure the tls port ex. `--tls-port=1636`, and provide a path to the pem files for the certificate `--tls-certificate=<path>` and the private key `--tls-private-key=<path>`.

## Outputs

This will create an LDAP tree that looks like this:

```ldif
dn: DC=<your domain>
objectClass: dcObject

dn: OU=users,DC=<your domain>
objectClass: organizationalUnit
ou: users

dn: OU=groups,DC=<your domain>
objectClass: organizationalUnit
ou: groups
```

Each user will have an entry like

```ldif
dn: CN=<user name>,OU=users,DC=<your domain>
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
objectClass: posixAccount
objectClass: top
<user data fields here>
memberOf: <DN for each group that this user belongs to>
```

Each group will have an entry like

```ldif
dn: CN=<group name>,OU=groups,DC=<your domain>
objectClass: groupOfNames
objectClass: posixGroup
objectClass: top
<group data fields here>
member: <DN for each user belonging to this group>
```

## Primary groups

:exclamation: You can disable the creation of mirrored groups with the `--disable-primary-groups` command line option :exclamation:

Apricot creates an associated group for each user, which acts as its POSIX user primary group.

For example:

```ldif
dn: CN=sherlock.holmes,OU=users,DC=<your domain>
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
objectClass: posixAccount
objectClass: top
...
memberOf: CN=sherlock.holmes,OU=groups,DC=<your domain>
...
```

will have an associated group

```ldif
dn: CN=sherlock.holmes,OU=groups,DC=<your domain>
objectClass: groupOfNames
objectClass: posixGroup
objectClass: top
...
member: CN=sherlock.holmes,OU=users,DC=<your domain>
...
```

## Mirrored groups

:exclamation: You can disable the creation of mirrored groups with the `--disable-mirrored-groups` command line option :exclamation:

Each group of users will have an associated group-of-groups where each user in the group will have its user primary group in the group-of-groups.
Note that these groups-of-groups are **not** `posixGroup`s as POSIX does not allow nested groups.

For example:

```ldif
dn:CN=Detectives,OU=groups,DC=<your domain>
objectClass: groupOfNames
objectClass: posixGroup
objectClass: top
...
member: CN=sherlock.holmes,OU=users,DC=<your domain>
...
```

will have an associated group-of-groups

```ldif
dn: CN=Primary user groups for Detectives,OU=groups,DC=<your domain>
objectClass: groupOfNames
objectClass: top
...
member: CN=sherlock.holmes,OU=groups,DC=<your domain>
...
```

This allows a user to make a request for "all primary user groups needed by members of group X" without getting a large number of primary user groups for unrelated users. To do this, you will need an LDAP request that looks like:

```ldif
(&(objectClass=posixGroup)(|(CN=Detectives)(memberOf=Primary user groups for Detectives)))
```

which will return:

```ldif
dn:CN=Detectives,OU=groups,DC=<your domain>
objectClass: groupOfNames
objectClass: posixGroup
objectClass: top
...
member: CN=sherlock.holmes,OU=users,DC=<your domain>
...

dn: CN=sherlock.holmes,OU=groups,DC=<your domain>
objectClass: groupOfNames
objectClass: posixGroup
objectClass: top
...
member: CN=sherlock.holmes,OU=users,DC=<your domain>
...
```

## OpenID Connect

Instructions for specific OpenID Connect backends below.

### Microsoft Entra

You will need to use the following command line arguments:

```bash
--backend MicrosoftEntra --entra-tenant-id "<your tenant ID>"
```

You will need to register an application to interact with `Microsoft Entra`.
Do this as follows:

- Create a new `App Registration` in your `Microsoft Entra`.
    - Set the name to whatever you choose (e.g. `apricot`)
    - Set access to `Accounts in this organizational directory only`.
    - Set `Redirect URI` to `Public client/native (mobile & desktop)` with a value of `urn:ietf:wg:oauth:2.0:oob`
- Under `Certificates & secrets` add a `New client secret`
    - Set the description to whatever you choose (e.g. `Apricot Authentication Secret`)
    - Set the expiry time to whatever is relevant for your use-case
    - You **must** record the value of this secret at **creation time**, as it will not be visible later.
- Under `API permissions`:
    - Enable the following permissions:
        - `Microsoft Graph` > `User.Read.All` (application)
        - `Microsoft Graph` > `GroupMember.Read.All` (application)
        - `Microsoft Graph` > `User.Read.All` (delegated)
    - Select this and click the `Grant admin consent` button (otherwise each user will need to manually consent)

### Keycloak

You will need to use the following command line arguments:

```bash
--backend Keycloak --keycloak-base-url "<your hostname>/<path to keycloak>" --keycloak-realm "<your realm>"
```

You will need to register an application to interact with `Keycloak`.
Do this as follows:

- Create a new `Client` in your `Keycloak` instance.
    - Set the name to whatever you choose (e.g. `apricot`)
    - Enable `Client authentication`
    - Enable the following authentication flows and disable the rest:
        - Direct access grants
        - Service account roles
- Under `Credentials` copy `client secret`
- Under `Service account roles`:
    - Click on `Assign role` then `Filter by clients`
    - Assign the following roles:
        - `realm-management` > `view-users`
        - `realm-management` > `manage-users`
        - `realm-management` > `query-groups`
        - `realm-management` > `query-users`
