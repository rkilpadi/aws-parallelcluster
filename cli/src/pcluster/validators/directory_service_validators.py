# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "LICENSE.txt" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and
# limitations under the License.

import re
from urllib.parse import urlparse

from pcluster.validators.common import FailureLevel, Validator


class DomainAddrValidator(Validator):
    """Domain address validator."""

    def _validate(self, domain_addr, additional_sssd_configs):
        """Warn user when ldap is used for the protocol instead of ldaps."""
        domain_addr_scheme = urlparse(domain_addr).scheme
        default_domain_addr_scheme = "ldaps"
        supported_domain_addr_schemes = (default_domain_addr_scheme, "ldap")
        if not domain_addr_scheme:
            self._add_failure(
                f"No protocol specified. Assuming the use of '{default_domain_addr_scheme}'",
                FailureLevel.WARNING,
            )
        elif domain_addr_scheme not in supported_domain_addr_schemes:
            self._add_failure(
                f"Unsupported protocol '{domain_addr_scheme}'. Supported protocols are: "
                + " ".join(supported_domain_addr_schemes),
                FailureLevel.WARNING,
            )
        elif domain_addr_scheme == "ldap":
            warning_message = "The use of the ldaps protocol is strongly encouraged for security reasons."
            tls_disabled = (
                str(additional_sssd_configs.get("ldap_auth_disable_tls_never_use_in_production", "false")).lower()
                == "true"
            )
            if not tls_disabled:
                warning_message += (
                    " When using ldap, the additional SSSD config is required: "
                    "'ldap_auth_disable_tls_never_use_in_production: true'."
                )
            self._add_failure(warning_message, FailureLevel.WARNING)


class DomainNameValidator(Validator):
    """Domain name validator."""

    FQDN_PATTERN = "^([a-zA-Z0-9_-]+)(\\.[a-zA-Z0-9_-]+)*$"
    LDAP_DN_PATTERN = "^((DC|dc)=[a-zA-Z0-9_-]+)(,(DC|dc)=[a-zA-Z0-9_-]+)*$"

    def _validate(self, domain_name):
        """Validate that domain address is a Fully Qualified Domain Name (FQDN) or a LDAP Distinguished Name (DN)."""
        match = re.match(DomainNameValidator.FQDN_PATTERN, domain_name) or re.match(
            DomainNameValidator.LDAP_DN_PATTERN, domain_name
        )
        if not match:
            self._add_failure(
                "Unsupported domain address format. "
                "Supported formats are FQDN (corp.example.com) or LDAP Distinguished Name (DC=corp,DC=example,DC=com).",
                FailureLevel.ERROR,
            )


class LdapTlsReqCertValidator(Validator):
    """LDAP TLS require certificate parameter validator."""

    def _validate(self, ldap_tls_reqcert):
        """Warn user of potentially insecure configurations."""
        values_requiring_cert_validation = ("hard", "demand")
        if ldap_tls_reqcert not in values_requiring_cert_validation:
            self._add_failure(
                f"For security reasons it's recommended to use {' or '.join(values_requiring_cert_validation)}",
                FailureLevel.WARNING,
            )