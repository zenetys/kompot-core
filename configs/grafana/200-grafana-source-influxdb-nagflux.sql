-- Test OK on grafana 9.2.4
-- Test OK on grafana 9.5.2

insert into data_source (
    id, org_id, version, type, name, access, url, password, user,
    database, basic_auth, basic_auth_user, basic_auth_password, is_default,
    json_data, created, updated, with_credentials, secure_json_data, read_only, uid
) values (
    1, 1, 1, 'influxdb', 'influxdb/nagflux', 'proxy', 'http://127.0.0.1:8086', '', '',
    'nagflux', 0, '', '', 1,
    '{}', datetime(), datetime(), 0, '{}', 0, 'IHQqRqynk'
)
