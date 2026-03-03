## Run KOMPOT as Podman container and systemd service

Prefer podman over docker for its integration with systemd, this is the recommended method for running KOMPOT as container.

**Installation:**

Run as systemd service with podman:

```
dnf --setopt install_weak_deps=0 install podman
curl -o /etc/containers/systemd/kompot.container \
    https://raw.githubusercontent.com/zenetys/docker-kompot/refs/heads/master/misc/kompot.container
systemctl daemon-reload
systemctl start kompot
systemctl enable kompot
```

Notes:

* Initial start may take some time: image download, Grafana initialization, etc.
* With no modification of kompot.container, the URL of the web interface is http://myhost:8083
* In order to change exposed ports, edit PublishPort directives in kompot.container, then issue `systemctl daemon-reload` and restart the container with `systemctl restart kompot`.

**Needed to enable the centreon-vmware service:**

In order to start the centreon_vmware service, Perl modules from VMware vSphere and vsan SDKs are required. Create a `system` directory in the `/etc/kompot/` volume; put the tarball (vSphere SDK) and zip (vsan SDK) in that directory, then restart the container.

The SDKs can be downloaded from Broadcom website :

* https://developer.broadcom.com/sdks/vsphere-perl-sdk/latest
* https://developer.broadcom.com/sdks/vsan-management-sdk-for-perl/latest
