# Apricot

`Apricot` is a proxy for delegating LDAP requests to an OpenID Connect backend.
The name is a slightly tortured acronym for: LD**A**P **pr**oxy for Open**I**D **Co**nnec**t**.

## Usage

Start the `Apricot` server on port 1389 by running:

```bash
python run.py --client-id "<your client ID>" --client-secret "<your client secret>" --backend "<your backend>" --port 1389 --domain "<your domain name>" --redis-host "<your Redis server>"
```

Alternatively, you can run in Docker by editing `docker/docker-compose.yaml` and running:

```bash
docker compose up
```

from the `docker` directory.

### Using Redis [Optional]

You can use a Redis server to store generated `uidNumber` and `gidNumber` values in a more persistent way.
To do this, you will need to provide the `--redis-host` and `--redis-port` arguments to `run.py`.

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
objectClass: inetuser
objectClass: person
objectClass: posixAccount
objectClass: top
<user data fields here>
```

Each group will have an entry like

```ldif
dn: CN=<group name>,OU=groups,DC=<your domain>
objectClass: groupOfNames
objectClass: posixGroup
objectClass: top
<group data fields here>
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
    - Ensure that the following permissions are enabled
        - `Microsoft Graph` > `User.Read.All` (application)
        - `Microsoft Graph` > `GroupMember.Read.All` (application)
        - `Microsoft Graph` > `User.Read.All` (delegated)
    - Select this and click the `Grant admin consent` button (otherwise manual consent is needed from each user)
