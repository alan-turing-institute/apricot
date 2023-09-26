from ldaptor.interfaces import IConnectedLDAPEntry, ILDAPEntry
from ldaptor.protocols.ldap.distinguishedname import DistinguishedName
from twisted.internet import defer
from twisted.python import log
from zope.interface import implementer

from apricot.proxied_ldap_entry import ProxiedLDAPEntry


@implementer(IConnectedLDAPEntry)
class LDAPLookupTree:
    def lookup(self, dn: DistinguishedName | str) -> defer.Deferred[ILDAPEntry]:
        """
        Lookup the referred to by dn.

        @return: A Deferred returning an ILDAPEntry, or failing with e.g.
        LDAPNoSuchObject.
        """

        def _lookup(dn: DistinguishedName) -> ProxiedLDAPEntry:
            return ProxiedLDAPEntry(dn, {})

        if not isinstance(dn, DistinguishedName):
            dn = DistinguishedName(stringValue=dn)
        return defer.maybeDeferred(_lookup, dn)
