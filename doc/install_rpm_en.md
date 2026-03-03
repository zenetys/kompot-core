## Install KOMPOT from RPM package

**Requirements:**

* Distribution RedHat EL 9 or clone
* For now SELinux must be disabled on the system

**Installation:**

RPM packages are available in ZENETYS yum repositories.

```
dnf update
dnf --setopt install_weak_deps=0 install epel-release 'dnf-command(config-manager)'
crb enable
(cd /etc/yum.repos.d; curl -OL https://packages.zenetys.com/projects/kompot/latest/redhat/kompot.repo)
rpm --import https://rpm.grafana.com/gpg.key
rpm --import https://repos.influxdata.com/influxdata-archive.key
dnf --setopt install_weak_deps=0 install kompot
/opt/kompot/bin/init-kompot restart
```

**Add puppeteer support:**

Puppeteer is not installed by default because it requires a lot of dependencies while must users don't need it. To install it, run:

```
dnf module enable nodejs:18
dnf --setopt install_weak_deps=0 install puppeteer
```

**Needed to start the centreon-vmware service:**

In order to start the centreon_vmware service, Perl modules from VMware vSphere and VMware vsan SDKs must be installed on the system. The SDKs can be downloaded from Broadcom website :

* https://developer.broadcom.com/sdks/vsphere-perl-sdk/latest
* https://developer.broadcom.com/sdks/vsan-management-sdk-for-perl/latest

An helper script is provided to install the modules, eg:

```
dnf --setopt install_weak_deps=0 install unzip
/opt/centreon-vmware/share/install-vmware-perl-modules \
    --vsphere /tmp/VMware-vSphere-Perl-SDK-7.0.0-17698549.x86_64.tar.gz \
    --vsan /tmp/vsan-sdk-perl-8.0U3.zip
```

(Re)start the centreon_vmware service:

```
systemctl restart centreon_vmware
```
