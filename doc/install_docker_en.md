## Run KOMPOT as Docker container

We recommend [using podman](./install_podman_systemd_en.md) for its integration with systemd. That way KOMPOT is an application controled like any systemd service.

**Installation:**

Run with an auto-(re)start policy, ie. no systemd service integration:

```
docker run \
  --restart unless-stopped \
  --name kompot \
  --hostname kompot \
  --tmpfs /run \
  --tmpfs /tmp \
  --volume ~/app/kompot/etc:/etc/kompot \
  --volume ~/app/kompot/data:/var/lib/kompot \
  --volume ~/app/kompot/log:/var/log \
  --publish 0.0.0.0:8083:80/tcp \
  --publish 0.0.0.0:8084:443/tcp \
  --publish 0.0.0.0:2222:22/tcp \
  --publish 0.0.0.0:5514:514/udp \
  --publish 0.0.0.0:5514:514/tcp \
  --publish 0.0.0.0:1162:162/udp \
  zenetys/kompot
```

Note that initial start may take some time: image download, Grafana initialization, etc.

**Needed to enable the centreon-vmware service:**

In order to start the centreon_vmware service, Perl modules from VMware vSphere and vsan SDKs are required. Create a `system` directory in the `/etc/kompot/` volume; put the tarball (vSphere SDK) and zip (vsan SDK) in that directory, then restart the container.

The SDKs can be downloaded from Broadcom website :

* https://developer.broadcom.com/sdks/vsphere-perl-sdk/latest
* https://developer.broadcom.com/sdks/vsan-management-sdk-for-perl/latest
