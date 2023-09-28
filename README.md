# Apricot

`Apricot` is a proxy for delegating LDAP requests to an OpenID Connect backend.
The name is a slightly tortured acronym for: LD**A**P **pr**oxy for Open**I**D **Co**nnec**t**.

## Usage

Start the `Apricot` server on port 8080 by running:

```bash
python run.py --client-id "<your client ID>" --client-secret "<your client secret>" --tenant-id "<your tenant ID>" --backend MicrosoftEntra --port 8080
```

## OpenID Connect

Instructions for specific OpenID Connect backends below.


### Microsoft Entra

You will need to register an application to interact with `Microsoft Entra`.
Do this as follows:

- Create a new `App Registration` in your `Microsoft Entra`.
    - Set the name to whatever you choose (in this example we will use `apricot`)
    - Set access to `Accounts in this organizational directory only`.
    - Set `Redirect URI` to `Public client/native (mobile & desktop)` with a value of `urn:ietf:wg:oauth:2.0:oob`
- Under `Certificates & secrets` add a `New client secret`
    - Set the description to `Apricot Authentication Secret`
    - Set the expiry time to whatever is relevant for your use-case
    - You **must** record the value of this secret at **creation time**, as it will not be visible later.
- Under `API permissions`:
    - Ensure that the following permissions are enabled
        - `Microsoft Graph` > `User.Read.All` (application)
        - `Microsoft Graph` > `GroupMember.Read.All` (application)
    - Select this and click the `Grant admin consent` button (otherwise manual consent is needed from each user)
